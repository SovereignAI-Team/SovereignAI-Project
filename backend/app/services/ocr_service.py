"""OCR fallback for scanned PDFs: PyMuPDF renders pages, Tesseract reads them."""
from __future__ import annotations

import io
import logging
import shutil
from pathlib import Path

import fitz

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OCRUnavailableError(Exception):
    """Tesseract (or pytesseract/Pillow) is not installed."""


def _find_tesseract() -> str | None:
    cmd = get_settings().tesseract_cmd.strip()
    if cmd:
        return cmd if Path(cmd).exists() else None
    found = shutil.which("tesseract")
    if found:
        return found
    # Default Windows install location
    default = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    return str(default) if default.exists() else None


def ocr_status() -> tuple[bool, str]:
    try:
        import pytesseract  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        return False, "pytesseract/Pillow not installed (pip install pytesseract pillow)"
    path = _find_tesseract()
    if not path:
        return False, "Tesseract not found. Install it and/or set TESSERACT_CMD."
    return True, f"Tesseract found at {path}"


def ocr_pages(pdf_path: Path, page_numbers: list[int]) -> dict[int, str]:
    """Run OCR on the given 1-based pages. Returns {page_number: text}."""
    ok, detail = ocr_status()
    if not ok:
        raise OCRUnavailableError(
            f"This PDF looks scanned and needs OCR, but OCR is unavailable: {detail}"
        )
    import pytesseract
    from PIL import Image

    pytesseract.pytesseract.tesseract_cmd = _find_tesseract()  # type: ignore[assignment]
    dpi = get_settings().ocr_dpi
    results: dict[int, str] = {}
    with fitz.open(pdf_path) as doc:
        for number in page_numbers:
            page = doc[number - 1]
            pix = page.get_pixmap(dpi=dpi)
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            results[number] = pytesseract.image_to_string(image).strip()
            logger.info("OCR finished for page %d", number)
    return results
