from __future__ import annotations
from pathlib import Path
from typing import Any

from app.files.service import get_file  # get_file(db, user_id, file_id) -> File ORM or dict


def _field(obj: Any, name: str, default=None):
    """Return attribute `name` from ORM object or dict, with a default."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def summarize_document(db, user_id: str, file_id: str, max_chars: int = 800):
    meta = get_file(db, user_id, file_id)
    if not meta:
        return {"error": "file_not_found", "file_id": file_id}

    # Try extracted text field if your pipeline stores it (common names below).
    text = (
        _field(meta, "text")
        or _field(meta, "extracted_text")
        or ""
    )

    # Optional fallback: if nothing extracted and it's a .txt file, read from disk.
    if not text:
        path = _field(meta, "path")
        mime = (_field(meta, "mime_type") or "").lower()
        try:
            if path and (mime == "text/plain" or str(path).lower().endswith(".txt")):
                text = Path(path).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            # ignore read errors—just return empty summary
            pass

    text = (text or "").strip()
    summary = (text[:max_chars] + "...") if len(text) > max_chars else text
    return {"summary": summary, "length": len(text), "file_id": file_id}
