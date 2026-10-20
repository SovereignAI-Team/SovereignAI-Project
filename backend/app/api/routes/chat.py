from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.chat import AskRequest, AskResponse
from app.services import audit_service, local_llm, rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    if not request.question.strip():
        raise HTTPException(status_code=422, detail="Question must not be empty.")
    audit_service.record_event("question_asked", detail=f"docs={len(request.document_ids)} chars={len(request.question)}")
    try:
        return rag_service.ask(request.question, request.document_ids)
    except local_llm.LLMUnavailableError as exc:
        audit_service.record_event("question_error", detail=str(exc)[:120])
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error while answering")
        audit_service.record_event("question_error", detail=type(exc).__name__)
        raise HTTPException(status_code=500, detail="Unexpected error while answering the question.") from exc
