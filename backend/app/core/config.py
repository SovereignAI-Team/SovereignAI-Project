"""Application configuration.

All settings come from environment variables (or a `.env` file inside the
backend directory). Paths are resolved relative to the backend directory so the
app works no matter where it is launched from.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ directory (this file lives in backend/app/core/)
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SovereignAI"
    app_env: str = "development"
    backend_host: str = "127.0.0.1"
    backend_port: int = Field(default=8000, ge=1, le=65535)

    # SQLite database file. Relative paths are resolved against backend/.
    database_url: str = "sqlite:///./data/sovereignai.db"

    # Optional override for where uploads/indexes/logs are stored
    data_dir_path: str = Field(default="", validation_alias="DATA_DIR")

    # Local LLM served by Ollama
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_timeout_seconds: int = Field(default=180, ge=5, le=1800)

    # Local embedding model (downloaded once from Hugging Face, then cached)
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    max_upload_mb: int = Field(default=25, ge=1, le=500)
    top_k: int = Field(default=5, ge=1, le=20)

    # Chunking
    chunk_size: int = Field(default=900, ge=200, le=4000)  # characters
    chunk_overlap: int = Field(default=150, ge=0, le=1000)  # characters

    # Retrieval: chunks scoring below this cosine similarity are treated as
    # "not relevant". Tune if answers are refused too often / too rarely.
    min_relevance_score: float = Field(default=0.20, ge=-1.0, le=1.0)

    # OCR
    tesseract_cmd: str = ""  # optional full path to tesseract.exe
    ocr_min_chars_per_page: int = Field(default=20, ge=0)
    ocr_dpi: int = Field(default=200, ge=72, le=400)

    # Comma separated list of allowed browser origins (local frontend only)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @field_validator("chunk_overlap")
    @classmethod
    def _overlap_smaller_than_size(cls, v: int, info):  # type: ignore[no-untyped-def]
        size = info.data.get("chunk_size", 900)
        if v >= size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return v

    # ---- derived paths -------------------------------------------------
    @property
    def data_dir(self) -> Path:
        # DATA_DIR can relocate storage (used by the tests); default is backend/data
        return Path(self.data_dir_path).resolve() if self.data_dir_path else BACKEND_DIR / "data"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def extracted_dir(self) -> Path:
        return self.data_dir / "extracted"

    @property
    def indexes_dir(self) -> Path:
        return self.data_dir / "indexes"

    @property
    def audit_dir(self) -> Path:
        return self.data_dir / "audit_logs"

    @property
    def database_path(self) -> Path:
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            raise ValueError("Only sqlite:/// URLs are supported")
        raw = Path(self.database_url[len(prefix):])
        return raw if raw.is_absolute() else (BACKEND_DIR / raw).resolve()

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    def ensure_directories(self) -> None:
        for d in (self.uploads_dir, self.extracted_dir, self.indexes_dir, self.audit_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
