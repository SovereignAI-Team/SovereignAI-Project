"""Split page text into overlapping chunks that remember their page number."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.services.pdf_service import PageText


@dataclass
class Chunk:
    chunk_index: int
    page_number: int
    text: str


def _split_text(text: str, size: int, overlap: int) -> list[str]:
    """Split one page's text into windows of ~size characters.

    Tries to break at paragraph/sentence/space boundaries so chunks read well.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            window = text[start:end]
            # prefer to cut at a natural boundary in the last 30% of the window
            floor = int(size * 0.7)
            cut = -1
            for sep in ("\n\n", "\n", ". ", " "):
                pos = window.rfind(sep)
                if pos >= floor:
                    cut = pos + len(sep)
                    break
            if cut > 0:
                end = start + cut
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return pieces


def chunk_pages(pages: Sequence[PageText], size: int = 900, overlap: int = 150) -> list[Chunk]:
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    chunks: list[Chunk] = []
    for page in pages:
        for piece in _split_text(page.text, size, overlap):
            chunks.append(Chunk(chunk_index=len(chunks), page_number=page.page_number, text=piece))
    return chunks
