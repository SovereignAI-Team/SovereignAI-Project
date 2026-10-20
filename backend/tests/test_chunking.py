import pytest

from app.services.chunking_service import chunk_pages
from app.services.pdf_service import PageText


def test_short_page_is_single_chunk():
    chunks = chunk_pages([PageText(1, "short text")], size=500, overlap=50)
    assert len(chunks) == 1
    assert chunks[0].page_number == 1
    assert chunks[0].chunk_index == 0


def test_long_page_is_split_with_overlap_and_page_metadata():
    text = " ".join(f"word{i}" for i in range(600))
    chunks = chunk_pages([PageText(7, text)], size=300, overlap=60)
    assert len(chunks) > 3
    assert all(c.page_number == 7 for c in chunks)
    assert all(len(c.text) <= 300 for c in chunks)
    # consecutive chunks share some text (overlap)
    assert set(chunks[0].text.split()[-3:]) & set(chunks[1].text.split())
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_empty_pages_are_skipped_and_numbers_kept():
    chunks = chunk_pages([PageText(1, ""), PageText(2, "hello there")], size=500, overlap=50)
    assert len(chunks) == 1
    assert chunks[0].page_number == 2


def test_invalid_overlap_raises():
    with pytest.raises(ValueError):
        chunk_pages([PageText(1, "x")], size=100, overlap=100)
