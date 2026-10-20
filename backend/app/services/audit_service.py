"""Audit trail: records WHAT happened, never document contents or prompts."""
from __future__ import annotations

import json
import logging
from typing import Optional

from app.core.config import get_settings
from app.database.database import db_session
from app.database.models import now_iso

logger = logging.getLogger(__name__)


def record_event(event_type: str, document_id: Optional[str] = None, detail: str = "") -> None:
    """Write an audit event to SQLite and to a JSON-lines file.

    `detail` must be short metadata (counts, error class names, file sizes).
    """
    detail = detail[:300]
    ts = now_iso()
    try:
        with db_session() as conn:
            conn.execute(
                "INSERT INTO audit_events (timestamp, event_type, document_id, detail) VALUES (?, ?, ?, ?)",
                (ts, event_type, document_id, detail),
            )
        audit_dir = get_settings().audit_dir
        audit_dir.mkdir(parents=True, exist_ok=True)
        line = json.dumps(
            {"timestamp": ts, "event": event_type, "document_id": document_id, "detail": detail}
        )
        with open(audit_dir / "audit.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:  # auditing must never break the request
        logger.exception("Failed to write audit event %s", event_type)
