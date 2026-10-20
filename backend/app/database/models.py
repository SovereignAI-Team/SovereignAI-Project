"""Small data-access helpers for the SQLite tables defined in database.py."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

STATUS_PROCESSING = "processing"
STATUS_READY = "ready"
STATUS_FAILED = "failed"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class DocumentRecord:
    id: str
    original_name: str
    stored_path: str
    file_hash: str
    size_bytes: int
    page_count: int
    chunk_count: int
    status: str
    used_ocr: bool
    error_message: Optional[str]
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "DocumentRecord":
        return cls(
            id=row["id"],
            original_name=row["original_name"],
            stored_path=row["stored_path"],
            file_hash=row["file_hash"],
            size_bytes=row["size_bytes"],
            page_count=row["page_count"],
            chunk_count=row["chunk_count"],
            status=row["status"],
            used_ocr=bool(row["used_ocr"]),
            error_message=row["error_message"],
            created_at=row["created_at"],
        )


def insert_document(conn: sqlite3.Connection, *, doc_id: str, original_name: str,
                    stored_path: str, file_hash: str, size_bytes: int) -> None:
    conn.execute(
        "INSERT INTO documents (id, original_name, stored_path, file_hash, size_bytes, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (doc_id, original_name, stored_path, file_hash, size_bytes, STATUS_PROCESSING, now_iso()),
    )


def get_document(conn: sqlite3.Connection, doc_id: str) -> Optional[DocumentRecord]:
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    return DocumentRecord.from_row(row) if row else None


def list_documents(conn: sqlite3.Connection) -> list[DocumentRecord]:
    rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
    return [DocumentRecord.from_row(r) for r in rows]


def find_ready_document_by_hash(conn: sqlite3.Connection, file_hash: str) -> Optional[DocumentRecord]:
    row = conn.execute(
        "SELECT * FROM documents WHERE file_hash = ? AND status = ? LIMIT 1",
        (file_hash, STATUS_READY),
    ).fetchone()
    return DocumentRecord.from_row(row) if row else None


def mark_ready(conn: sqlite3.Connection, doc_id: str, page_count: int,
               chunk_count: int, used_ocr: bool) -> None:
    conn.execute(
        "UPDATE documents SET status = ?, page_count = ?, chunk_count = ?, used_ocr = ?, error_message = NULL "
        "WHERE id = ?",
        (STATUS_READY, page_count, chunk_count, int(used_ocr), doc_id),
    )


def mark_failed(conn: sqlite3.Connection, doc_id: str, message: str) -> None:
    conn.execute(
        "UPDATE documents SET status = ?, error_message = ? WHERE id = ?",
        (STATUS_FAILED, message[:500], doc_id),
    )


def delete_document_row(conn: sqlite3.Connection, doc_id: str) -> None:
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))  # chunks cascade


def insert_chunks(conn: sqlite3.Connection, doc_id: str,
                  chunks: list[tuple[int, int, str]]) -> None:
    """chunks: list of (chunk_index, page_number, text)."""
    conn.executemany(
        "INSERT INTO chunks (document_id, chunk_index, page_number, text) VALUES (?, ?, ?, ?)",
        [(doc_id, idx, page, text) for idx, page, text in chunks],
    )


def get_chunks(conn: sqlite3.Connection, doc_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT chunk_index, page_number, text FROM chunks WHERE document_id = ? ORDER BY chunk_index",
        (doc_id,),
    ).fetchall()
