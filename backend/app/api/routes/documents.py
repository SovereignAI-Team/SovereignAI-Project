from __future__ import annotations

import hashlib
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.database import models
from app.database.database import db_session
from app.schemas.documents import DeleteResponse, DocumentListResponse, DocumentOut, UploadResponse
from app.services import audit_service, pdf_service, rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


def _to_out(rec: models.DocumentRecord) -> DocumentOut:
    return DocumentOut(
        id=rec.id, original_name=rec.original_name, size_bytes=rec.size_bytes,
        page_count=rec.page_count, chunk_count=rec.chunk_count, status=rec.status,
        used_ocr=rec.used_ocr, error_message=rec.error_message, created_at=rec.created_at,
    )


@router.post("/upload", response_model=UploadResponse, status_code=201)
def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    s = get_settings()
    display_name = pdf_service.sanitize_filename(file.filename or "document.pdf")
    if not display_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF files are supported.")

    # Read at most limit+1 bytes so huge uploads are rejected without filling memory
    data = file.file.read(s.max_upload_bytes + 1)
    try:
        pdf_service.validate_pdf_bytes(data, s.max_upload_bytes)
    except pdf_service.PDFValidationError as exc:
        audit_service.record_event("upload_rejected", detail=type(exc).__name__)
        status = 413 if "too large" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc

    file_hash = hashlib.sha256(data).hexdigest()
    doc_id = pdf_service.new_document_id()
    stored_path = s.uploads_dir / f"{doc_id}.pdf"  # server-generated name only
    s.uploads_dir.mkdir(parents=True, exist_ok=True)
    stored_path.write_bytes(data)

    with db_session() as conn:
        existing = models.find_ready_document_by_hash(conn, file_hash)
        models.insert_document(
            conn, doc_id=doc_id, original_name=display_name, stored_path=str(stored_path),
            file_hash=file_hash, size_bytes=len(data),
        )
    audit_service.record_event("upload_received", doc_id, f"bytes={len(data)}")

    duplicate = False
    try:
        if existing is not None and rag_service.vector_store.index_exists(existing.id):
            # Identical file already indexed: reuse its chunks and index (no re-embedding)
            rag_service.clone_indexed_data(existing.id, doc_id)
            duplicate = True
        else:
            rag_service.ingest_pdf(doc_id, stored_path)
    except rag_service.IngestError as exc:
        with db_session() as conn:
            models.mark_failed(conn, doc_id, str(exc))
        audit_service.record_event("processing_failed", doc_id, type(exc.__cause__ or exc).__name__)
    except Exception as exc:
        logger.exception("Unexpected error while processing document")
        with db_session() as conn:
            models.mark_failed(conn, doc_id, "Unexpected error while processing the document.")
        audit_service.record_event("processing_failed", doc_id, type(exc).__name__)

    with db_session() as conn:
        rec = models.get_document(conn, doc_id)
    assert rec is not None
    if rec.status == models.STATUS_READY:
        audit_service.record_event("processing_complete", doc_id, f"pages={rec.page_count} chunks={rec.chunk_count}")
        message = "Document is already indexed (reused existing index)." if duplicate else "Document processed and ready."
    else:
        message = rec.error_message or "Processing failed."
    return UploadResponse(document=_to_out(rec), message=message, duplicate=duplicate)


@router.get("", response_model=DocumentListResponse)
def list_documents() -> DocumentListResponse:
    with db_session() as conn:
        return DocumentListResponse(documents=[_to_out(r) for r in models.list_documents(conn)])


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: str) -> DocumentOut:
    with db_session() as conn:
        rec = models.get_document(conn, document_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return _to_out(rec)


@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document(document_id: str) -> DeleteResponse:
    if not document_id.isalnum():
        raise HTTPException(status_code=404, detail="Document not found.")
    with db_session() as conn:
        rec = models.get_document(conn, document_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    rag_service.delete_document_data(document_id)
    audit_service.record_event("document_deleted", document_id)
    return DeleteResponse(id=document_id, deleted=True, message="Document and its data were deleted.")
