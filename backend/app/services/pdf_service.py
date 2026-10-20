"""PDF validation and text extraction with PyMuPDF."""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

PDF_MAGIC = b"%PDF-"


class PDFValidationError(Exception):
    """Raised when an uploaded file is not an acceptable PDF."""


@dataclass
class PageText:
    page_number: int  # 1-based
    text: str


def sanitize_filename(name: str) -> str:
    """Return a safe display name (no directories, no odd characters)."""
    name = name.replace("\\", "/").split("/")[-1]  # strip any path parts
    name = re.sub(r"[^\w.\- ()]", "_", name, flags=re.UNICODE).strip(" .")
    return (name or "document.pdf")[:120]


def new_document_id() -> str:
    return uuid.uuid4().hex


def validate_pdf_bytes(data: bytes, max_bytes: int) -> None:
    """Check size, magic bytes and that PyMuPDF can really open the file."""
    if not data:
        raise PDFValidationError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise PDFValidationError(f"File is too large (limit is {max_bytes // (1024 * 1024)} MB).")
    if not data.lstrip()[:5] == PDF_MAGIC and data[:1024].find(PDF_MAGIC) == -1:
        raise PDFValidationError("The file does not look like a PDF.")
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            if doc.needs_pass:
                raise PDFValidationError("Password-protected PDFs are not supported.")
            if doc.page_count == 0:
                raise PDFValidationError("The PDF has no pages.")
    except PDFValidationError:
        raise
    except Exception as exc:
        raise PDFValidationError("The PDF is corrupted or could not be opened.") from exc


def extract_pages(pdf_path: Path) -> list[PageText]:
    """Extract text for every page (including empty ones) preserving page numbers."""
    pages: list[PageText] = []
    with fitz.open(pdf_path) as doc:
        for index, page in enumerate(doc):
            text = page.get_text("text") or ""
            pages.append(PageText(page_number=index + 1, text=_clean(text)))
    return pages


def _clean(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
