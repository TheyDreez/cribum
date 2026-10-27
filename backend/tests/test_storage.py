import io
import os
import shutil
import tempfile
import pytest
from PIL import Image

from backend.services.storage import (
    MAX_FILE_BYTES,
    MAX_PIXELS,
    STORAGE_DIR,
    FileTooLargeError,
    InvalidImageError,
    StorageError,
    compute_sha256_bytes,
    ensure_storage_dir,
    get_image_path,
    read_upload_file_chunked,
    validate_and_save_image,
    validate_file_signature,
)


@pytest.fixture
def temp_storage_dir():
    """Fixture para isolar o diretório de armazenamento durante os testes."""
    orig_dir = STORAGE_DIR
    temp_dir = tempfile.mkdtemp()
    import backend.services.storage as storage_mod
    storage_mod.STORAGE_DIR = temp_dir
    yield temp_dir
    storage_mod.STORAGE_DIR = orig_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def _create_test_image_bytes(format="JPEG", mode="RGB", size=(100, 100)) -> bytes:
    img = Image.new(mode, size, color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_compute_sha256_bytes():
    data = b"test data"
    # echo -n "test data" | sha256sum
    expected = "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
    assert compute_sha256_bytes(data) == expected


def test_validate_file_signature():
    # JPEG magic bytes
    assert validate_file_signature(b"\xff\xd8\xff\xe0\x00\x10JFIF") is True
    # PNG magic bytes
    assert validate_file_signature(b"\x89PNG\r\n\x1a\n\x00\x00") is True
    # PDF magic bytes
    assert validate_file_signature(b"%PDF-1.4\n...") is True
    # Invalid magic bytes
    assert validate_file_signature(b"GIF89a") is False
    assert validate_file_signature(b"12") is False
    assert validate_file_signature(b"") is False


def test_ensure_storage_dir(temp_storage_dir):
    ensure_storage_dir()
    assert os.path.exists(temp_storage_dir)


def test_validate_and_save_image_jpeg(temp_storage_dir):
    img_bytes = _create_test_image_bytes(format="JPEG", mode="RGB", size=(200, 150))
    key, content_hash, w, h, media_type = validate_and_save_image(
        img_bytes, "test.jpg", "image/jpeg"
    )

    assert key.endswith(".jpg")
    assert len(content_hash) == 64
    assert w == 200
    assert h == 150
    assert media_type == "image/jpeg"

    saved_path = os.path.join(temp_storage_dir, key)
    assert os.path.exists(saved_path)
    with open(saved_path, "rb") as f:
        saved_bytes = f.read()
    assert compute_sha256_bytes(saved_bytes) == content_hash


def test_validate_and_save_image_png(temp_storage_dir):
    img_bytes = _create_test_image_bytes(format="PNG", mode="RGBA", size=(100, 100))
    key, content_hash, w, h, media_type = validate_and_save_image(
        img_bytes, "test.png", "image/png"
    )

    assert key.endswith(".png")
    assert len(content_hash) == 64
    assert w == 100
    assert h == 100
    assert media_type == "image/png"

    saved_path = os.path.join(temp_storage_dir, key)
    assert os.path.exists(saved_path)


def test_validate_and_save_image_jpeg_rgba_conversion(temp_storage_dir):
    # Imagem JPEG com modo RGBA (por exemplo, Pillow pode criar)
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    # Salva como JPEG (Pillow converterá ou precisará ser convertido)
    img.convert("RGB").save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    key, content_hash, w, h, media_type = validate_and_save_image(
        img_bytes, "rgba_test.jpg"
    )
    assert media_type == "image/jpeg"
    saved_path = os.path.join(temp_storage_dir, key)
    with Image.open(saved_path) as saved_img:
        assert saved_img.mode == "RGB"


def test_validate_and_save_image_empty_bytes():
    with pytest.raises(InvalidImageError, match="Arquivo vazio"):
        validate_and_save_image(b"", "empty.jpg")


def test_validate_and_save_image_file_too_large():
    fake_large_bytes = b"\xff\xd8\xff" + b"0" * (MAX_FILE_BYTES + 1)
    with pytest.raises(FileTooLargeError, match="excede o limite máximo"):
        validate_and_save_image(fake_large_bytes, "large.jpg")


def test_validate_and_save_image_invalid_signature():
    bad_bytes = b"EXIF_HEADER_FAKE_DATA"
    with pytest.raises(InvalidImageError, match="assinatura binária incompatível"):
        validate_and_save_image(bad_bytes, "fake.jpg")


def test_validate_and_save_image_corrupted_image():
    # Começa com assinatura JPEG válida, mas o resto é lixo corrompido
    corrupted_bytes = b"\xff\xd8\xff" + b"CORRUPTED_DATA_PADDING_FOR_TESTING"
    with pytest.raises(InvalidImageError, match="não é uma imagem válida"):
        validate_and_save_image(corrupted_bytes, "corrupt.jpg")


def test_validate_and_save_image_unsupported_format(temp_storage_dir):
    # PDF possui magic bytes (%PDF-) aceitos no validate_file_signature, mas Pillow não suporta JPEG/PNG para ele
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    with pytest.raises(InvalidImageError, match="não é uma imagem válida"):
        validate_and_save_image(pdf_bytes, "doc.pdf")


def test_validate_and_save_image_decompression_bomb(temp_storage_dir, monkeypatch):
    # Reduz temporariamente MAX_PIXELS para testar a proteção contra decompression bomb
    import backend.services.storage as storage_mod
    monkeypatch.setattr(storage_mod, "MAX_PIXELS", 5000)

    # Cria imagem de 100x100 = 10,000 pixels > 5,000 pixels
    img_bytes = _create_test_image_bytes(format="JPEG", size=(100, 100))
    with pytest.raises(InvalidImageError, match="excede o limite de segurança"):
        validate_and_save_image(img_bytes, "bomb.jpg")


def test_get_image_path_success(temp_storage_dir):
    test_file = os.path.join(temp_storage_dir, "file123.jpg")
    with open(test_file, "w") as f:
        f.write("dummy")

    path = get_image_path("file123.jpg")
    assert path == test_file


def test_get_image_path_not_found(temp_storage_dir):
    with pytest.raises(FileNotFoundError, match="Arquivo não encontrado"):
        get_image_path("non_existent_file.jpg")


def test_get_image_path_path_traversal_prevention(temp_storage_dir):
    # Se tentar passar path traversal, os.path.basename previne
    with pytest.raises(FileNotFoundError):
        get_image_path("../../../etc/passwd")


@pytest.mark.asyncio
async def test_read_upload_file_chunked_success():
    class DummyUploadFile:
        def __init__(self, data: bytes):
            self.stream = io.BytesIO(data)

        async def read(self, chunk_size: int) -> bytes:
            return self.stream.read(chunk_size)

    sample_data = b"A" * (128 * 1024)  # 128 KB
    dummy = DummyUploadFile(sample_data)
    result = await read_upload_file_chunked(dummy, max_bytes=256 * 1024)
    assert result == sample_data


@pytest.mark.asyncio
async def test_read_upload_file_chunked_too_large():
    class DummyUploadFile:
        def __init__(self, data: bytes):
            self.stream = io.BytesIO(data)

        async def read(self, chunk_size: int) -> bytes:
            return self.stream.read(chunk_size)

    sample_data = b"B" * (200 * 1024)  # 200 KB
    dummy = DummyUploadFile(sample_data)
    with pytest.raises(FileTooLargeError, match="excede o limite máximo"):
        await read_upload_file_chunked(dummy, max_bytes=100 * 1024)
