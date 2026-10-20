from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    document_ids: list[str] = Field(min_length=1, max_length=50)


class Citation(BaseModel):
    document_id: str
    document_name: str
    page_number: int
    excerpt: str
    score: float


class AskResponse(BaseModel):
    answer: str
    answered: bool  # False when the document content does not support an answer
    citations: list[Citation]
    model: str


class ComponentStatus(BaseModel):
    ok: bool
    detail: str


class HealthResponse(BaseModel):
    status: str  # ok | degraded
    backend: ComponentStatus
    database: ComponentStatus
    embedding: ComponentStatus
    llm: ComponentStatus
    ocr: Optional[ComponentStatus] = None
