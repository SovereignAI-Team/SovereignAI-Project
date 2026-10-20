from __future__ import annotations

import logging

from fastapi import APIRouter

from app.schemas.chat import ComponentStatus, HealthResponse
from app.services import embedding_service, local_llm, ocr_service
from app.database.database import db_session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        with db_session() as conn:
            conn.execute("SELECT 1")
        db = ComponentStatus(ok=True, detail="SQLite OK")
    except Exception:
        db = ComponentStatus(ok=False, detail="Database unavailable")

    emb_ok, emb_detail = embedding_service.embedding_status()
    llm_ok, llm_detail = local_llm.llm_status()
    ocr_ok, ocr_detail = ocr_service.ocr_status()

    components = [db.ok, emb_ok, llm_ok]
    return HealthResponse(
        status="ok" if all(components) else "degraded",
        backend=ComponentStatus(ok=True, detail="API running"),
        database=db,
        embedding=ComponentStatus(ok=emb_ok, detail=emb_detail),
        llm=ComponentStatus(ok=llm_ok, detail=llm_detail),
        ocr=ComponentStatus(ok=ocr_ok, detail=ocr_detail),  # optional feature
    )
