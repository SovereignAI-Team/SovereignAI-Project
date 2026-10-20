from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    original_name: str
    size_bytes: int
    page_count: int
    chunk_count: int
    status: str  # processing | ready | failed
    used_ocr: bool
    error_message: Optional[str] = None
    created_at: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentOut]


class UploadResponse(BaseModel):
    document: DocumentOut
    message: str
    duplicate: bool = False


class DeleteResponse(BaseModel):
    id: str
    deleted: bool
    message: str
