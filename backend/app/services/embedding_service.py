"""Local embeddings with Sentence Transformers (model is loaded lazily, once)."""
from __future__ import annotations

import logging
import threading
from typing import Optional

import numpy as np

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_model = None
_lock = threading.Lock()
_load_error: Optional[str] = None


def _get_model():
    global _model, _load_error
    if _model is not None:
        return _model
    with _lock:
        if _model is None:
            try:
                from sentence_transformers import SentenceTransformer

                name = get_settings().embedding_model
                logger.info("Loading embedding model %s (first run downloads it)", name)
                _model = SentenceTransformer(name)
                _load_error = None
            except Exception as exc:
                _load_error = f"{type(exc).__name__}: {exc}"
                raise
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Return L2-normalised float32 embeddings, shape (n, dim)."""
    model = _get_model()
    vectors = model.encode(
        texts,
        batch_size=32,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(vectors, dtype="float32")


def embedding_status(load: bool = False) -> tuple[bool, str]:
    """Report embedding model state. `load=True` forces loading the model."""
    name = get_settings().embedding_model
    if _model is not None:
        return True, f"{name} loaded"
    if load:
        try:
            _get_model()
            return True, f"{name} loaded"
        except Exception as exc:
            return False, f"Could not load {name}: {type(exc).__name__}"
    if _load_error:
        return False, f"Failed to load {name}: {_load_error[:120]}"
    return True, f"{name} (loads on first use)"
