import pytest

from app.services import pdf_service
from tests.conftest import make_pdf_bytes


def test_sanitize_filename_strips_paths_and_odd_chars():
    assert pdf_service.sanitize_filename("../../etc/passwd.pdf") == "passwd.pdf"
    assert pdf_service.sanitize_filename("C:\\temp\\my<doc>.pdf") == "my_doc_.pdf"
    assert pdf_service.sanitize_filename("") == "document.pdf"


def test_validate_rejects_empty_non_pdf_and_oversize():
    with pytest.raises(pdf_service.PDFValidationError):
        pdf_service.validate_pdf_bytes(b"", 1000)
    with pytest.raises(pdf_service.PDFValidationError):
        pdf_service.validate_pdf_bytes(b"hello world, not a pdf", 1000)
    with pytest.raises(pdf_service.PDFValidationError):
        pdf_service.validate_pdf_bytes(make_pdf_bytes(["x"]), 10)


def test_validate_rejects_corrupt_pdf():
    with pytest.raises(pdf_service.PDFValidationError):
        pdf_service.validate_pdf_bytes(b"%PDF-1.4 this is broken", 10_000)


def test_validate_accepts_real_pdf():
    pdf_service.validate_pdf_bytes(make_pdf_bytes(["hello"]), 1_000_000)


def test_extract_pages_preserves_page_numbers(tmp_path):
    path = tmp_path / "a.pdf"
    path.write_bytes(make_pdf_bytes(["first page text", "", "third page text"]))
    pages = pdf_service.extract_pages(path)
    assert [p.page_number for p in pages] == [1, 2, 3]
    assert "first page" in pages[0].text
    assert pages[1].text == ""
    assert "third page" in pages[2].text
