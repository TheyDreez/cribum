import hashlib
import io
import os
import uuid
from typing import Optional, Tuple
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_PIXELS = 40_000_000            # 40 Megapixels (proteção contra decompression bomb)
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}
STORAGE_DIR = os.path.abspath("backend/data/storage")


class StorageError(Exception):
    pass


class InvalidImageError(StorageError):
    pass


class FileTooLargeError(StorageError):
    pass


def ensure_storage_dir():
    os.makedirs(STORAGE_DIR, exist_ok=True)


def compute_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_and_save_image(
    file_bytes: bytes,
    original_filename: str,
    content_type: Optional[str] = None
) -> Tuple[str, str, int, int, str]:
    """
    Valida e sanitiza o upload da imagem médica:
    - Validação de tamanho máximo em bytes e pixels.
    - Validação de integridade real via Pillow.
    - Normalização de orientação EXIF e remoção de metadados desnecessários.
    - Geração de nome interno seguro (UUID) imune a path traversal.
    - Cálculo do hash criptográfico SHA-256.

    Retorna:
        (storage_key, content_hash, width, height, media_type)
    """
    ensure_storage_dir()

    # 1. Checagem de tamanho de arquivo
    if len(file_bytes) > MAX_FILE_BYTES:
        raise FileTooLargeError(f"Arquivo excede o limite máximo permitido de {MAX_FILE_BYTES // (1024*1024)}MB.")

    if len(file_bytes) == 0:
        raise InvalidImageError("Arquivo vazio.")

    # 2. Verificação de integridade e tipo real da imagem
    try:
        # Image.open não carrega tudo em memória até chamar load() ou verify()
        image = Image.open(io.BytesIO(file_bytes))
        image.verify()
    except (UnidentifiedImageError, Exception) as exc:
        raise InvalidImageError(f"Conteúdo do arquivo não é uma imagem válida: {str(exc)}") from exc

    # Reabre a imagem após verify() para operações de normalização
    image = Image.open(io.BytesIO(file_bytes))

    format_name = (image.format or "").upper()
    if format_name not in ("JPEG", "JPG", "PNG"):
        raise InvalidImageError(f"Formato de imagem não suportado: {format_name}. Apenas PNG e JPEG são aceitos.")

    media_type = "image/png" if format_name == "PNG" else "image/jpeg"

    # 3. Proteção contra Decompression Bomb (excesso de pixels)
    width, height = image.size
    if (width * height) > MAX_PIXELS:
        raise InvalidImageError(f"Resolução ({width}x{height}) excede o limite de segurança de {MAX_PIXELS} pixels.")

    # 4. Normalização de orientação EXIF e conversão de modo de cor
    try:
        image = ImageOps.exif_transpose(image)
        width, height = image.size
    except Exception:
        pass  # se não houver exif válido, mantém a imagem como está

    # Se for RGBA e salvar como JPEG, converte para RGB
    if format_name in ("JPEG", "JPG") and image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    # 5. Salva a imagem sanitizada sem metadados indesejados
    safe_id = str(uuid.uuid4())
    ext = ".png" if format_name == "PNG" else ".jpg"
    safe_filename = f"{safe_id}{ext}"
    safe_path = os.path.join(STORAGE_DIR, safe_filename)

    # Previne path traversal verificando se o caminho resultante está dentro de STORAGE_DIR
    if not os.path.commonpath([STORAGE_DIR, safe_path]) == STORAGE_DIR:
        raise StorageError("Tentativa de path traversal detectada.")

    output_buffer = io.BytesIO()
    if format_name == "PNG":
        image.save(output_buffer, format="PNG", optimize=True)
    else:
        image.save(output_buffer, format="JPEG", quality=92, optimize=True)

    sanitized_bytes = output_buffer.getvalue()
    content_hash = compute_sha256_bytes(sanitized_bytes)

    with open(safe_path, "wb") as f:
        f.write(sanitized_bytes)

    return safe_filename, content_hash, width, height, media_type


def get_image_path(storage_key: str) -> str:
    """Recupera caminho absoluto do arquivo garantindo contenção no diretório de armazenamento."""
    clean_key = os.path.basename(storage_key)
    full_path = os.path.join(STORAGE_DIR, clean_key)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {storage_key}")
    return full_path


async def read_upload_file_chunked(file, max_bytes: int = MAX_FILE_BYTES) -> bytes:
    """
    Lê o upload em blocos limitados (64 KB) e aborta imediatamente se o tamanho
    acumulado exceder max_bytes, evitando buffering descontrolado de arquivos gigantescos na memória.
    """
    buffer = bytearray()
    chunk_size = 64 * 1024  # 64 KB
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise FileTooLargeError(
                f"Arquivo excede o limite máximo permitido de {max_bytes // (1024 * 1024)}MB."
            )
    return bytes(buffer)

