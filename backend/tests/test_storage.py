import pytest
from backend.services.storage import validate_file_signature


def test_validate_file_signature_valid_jpeg():
    """Valida retorno True para arquivo com header JPEG (\xff\xd8\xff)."""
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    assert validate_file_signature(jpeg_bytes) is True


def test_validate_file_signature_valid_png():
    """Valida retorno True para arquivo com header PNG (\x89PNG\r\n\x1a\n)."""
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    assert validate_file_signature(png_bytes) is True


def test_validate_file_signature_valid_pdf():
    """Valida retorno True para arquivo com header PDF (%PDF-)."""
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n"
    assert validate_file_signature(pdf_bytes) is True


def test_validate_file_signature_empty_or_none():
    """Valida retorno False para conteúdo vazio ou None."""
    assert validate_file_signature(b"") is False
    assert validate_file_signature(None) is False


def test_validate_file_signature_short_content():
    """Valida retorno False para dados com menos de 3 bytes."""
    assert validate_file_signature(b"\xff") is False
    assert validate_file_signature(b"\xff\xd8") is False
    assert validate_file_signature(b"ab") is False


def test_validate_file_signature_invalid_magic_bytes():
    """Valida retorno False para assinaturas não suportadas ou dados arbitrários."""
    assert validate_file_signature(b"GIF89a123") is False
    assert validate_file_signature(b"Hello World!") is False
    assert validate_file_signature(b"\x00\x00\x00\x00\x00") is False
