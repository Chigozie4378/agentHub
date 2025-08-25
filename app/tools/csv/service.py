# app/tools/csv/service.py
from __future__ import annotations
import csv, os
from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.files.service import get_file  # def get_file(db, user_id, file_id) -> dict (or ORM with .path)
from app.shared.storage import ensure_dir  # small helper you likely have; else os.makedirs

def _meta_path(meta: Any) -> str | None:
    """Robustly extract a usable file path from your File meta/ORM."""
    if not meta:
        return None
    # dict-like
    if isinstance(meta, dict):
        return meta.get("path") or meta.get("artifact_path") or meta.get("filepath")
    # ORM-ish
    return getattr(meta, "path", None) or getattr(meta, "artifact_path", None) or getattr(meta, "filepath", None)

def preview_csv(db: Session, user_id: str, file_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    Reads a CSV from the uploaded file storage, returns headers and up to `limit` rows.
    Also writes a normalized copy to artifacts and returns its path.
    """
    meta = get_file(db, user_id, file_id)
    if not meta:
        raise FileNotFoundError(f"File '{file_id}' not found for user '{user_id}'")

    src_path = _meta_path(meta)
    if not src_path or not os.path.exists(src_path):
        raise FileNotFoundError(f"Uploaded file path missing/not found for '{file_id}'")

    headers: List[str] = []
    rows: List[List[str]] = []

    # Read CSV
    with open(src_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader, [])
        except Exception:
            headers = []
        for i, row in enumerate(reader):
            if i >= limit:
                break
            rows.append(row)

    # Write normalized CSV (headers + rows we actually returned)
    norm_dir = os.path.join("storage", "artifacts", "csv")
    ensure_dir(norm_dir)
    norm_path = os.path.join(norm_dir, f"normalized_{file_id}.csv")
    with open(norm_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if headers:
            w.writerow(headers)
        w.writerows(rows)

    return {
        "ok": True,
        "headers": headers,
        "rows": rows,
        "normalized_csv_path": norm_path,
        "source_path": src_path,
    }
