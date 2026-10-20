"""One FAISS index per document, persisted to data/indexes/<document_id>.faiss.

Vectors are L2-normalised, so inner product == cosine similarity.
Row i of the index corresponds to chunk_index i of that document in SQLite.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SearchHit:
    document_id: str
    chunk_index: int
    score: float


def _index_path(document_id: str) -> Path:
    # document ids are server-generated hex; reject anything else (path traversal)
    if not document_id.isalnum():
        raise ValueError("Invalid document id")
    return get_settings().indexes_dir / f"{document_id}.faiss"


def build_index(document_id: str, vectors: np.ndarray) -> None:
    if vectors.ndim != 2 or vectors.shape[0] == 0:
        raise ValueError("No vectors to index")
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    path = _index_path(document_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(path))


def index_exists(document_id: str) -> bool:
    return _index_path(document_id).exists()


def delete_index(document_id: str) -> None:
    path = _index_path(document_id)
    if path.exists():
        path.unlink()


def search(document_ids: list[str], query_vector: np.ndarray, top_k: int) -> list[SearchHit]:
    """Search every selected document's index and return the best hits overall."""
    query = np.asarray(query_vector, dtype="float32").reshape(1, -1)
    hits: list[SearchHit] = []
    for doc_id in document_ids:
        if not index_exists(doc_id):
            continue
        index = faiss.read_index(str(_index_path(doc_id)))
        if index.d != query.shape[1]:
            logger.warning("Embedding dimension mismatch for a document; re-upload it.")
            continue
        k = min(top_k, index.ntotal)
        if k == 0:
            continue
        scores, ids = index.search(query, k)
        for score, idx in zip(scores[0], ids[0]):
            if idx >= 0:
                hits.append(SearchHit(document_id=doc_id, chunk_index=int(idx), score=float(score)))
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:top_k]
