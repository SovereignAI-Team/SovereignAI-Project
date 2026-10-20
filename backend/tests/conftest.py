"""Shared test fixtures: isolated storage, fake embeddings, fake LLM (no models needed)."""
from __future__ import annotations

import hashlib
import re

import fitz
import numpy as np
import pytest

from app.core.config import get_settings

DIM = 1024  # large enough that unrelated words rarely collide in the hash buckets


def fake_embed(texts: list[str]) -> np.ndarray:
    """Deterministic bag-of-words hashing embedding (normalised)."""
    out = np.zeros((len(texts), DIM), dtype="float32")
    for i, text in enumerate(texts):
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            out[i, h % DIM] += 1.0
        norm = np.linalg.norm(out[i])
        if norm > 0:
            out[i] /= norm
    return out


def make_pdf_bytes(pages: list[str]) -> bytes:
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'data' / 'test.db').as_posix()}")
    monkeypatch.setenv("MIN_RELEVANCE_SCORE", "0.2")
    get_settings.cache_clear()
    from app.database.database import init_db

    init_db()
    monkeypatch.setattr("app.services.embedding_service.embed_texts", fake_embed)
    yield
    get_settings.cache_clear()


@pytest.fixture
def fake_llm(monkeypatch):
    """Replace the Ollama call; records the prompts it receives."""
    calls: list[tuple[str, str]] = []

    def _generate(system: str, user: str) -> str:
        calls.append((system, user))
        return "The warranty period is 24 months (manual.pdf, p. 1)."

    monkeypatch.setattr("app.services.local_llm.generate", _generate)
    return calls


@pytest.fixture
def sample_pdf() -> bytes:
    return make_pdf_bytes(
        [
            "Warranty terms. The warranty period is 24 months from the date of purchase.",
            "Installation guide. Mount the unit on a flat wall using the supplied screws.",
        ]
    )
