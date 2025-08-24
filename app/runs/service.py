from typing import Tuple, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from datetime import datetime, timezone

from app.runs.models import Run, Step
from app.tools.schema_validator import require_valid  # <- you added earlier

# Optional: aliases for legacy callers that set "tool": "browser" / "email"
TOOL_ALIASES = {
    "browser": "browser.screenshot",
    "email": "email.draft_send",
    "pdf": "pdf.generate",
    "csv": "csv.preview",
    "places": "places.search",
    "search": "search.web",
    "download": "download.fetch",
    "summarize": "summarize.document",
    "sentiment": "sentiment.analyze",
    "todos.create": "todos.create",
    "todos.list": "todos.list",
    "todos.update": "todos.update",
    "todos.delete": "todos.delete",
    "notes.create": "notes.create",
    "notes.summarize": "notes.summarize",
    "reminders.create": "reminders.create",
    "calendar.create_event": "calendar.create_event",
    "calendar.update_event": "calendar.update_event",
    "calendar.delete_event": "calendar.delete_event",
    "calendar.list_events": "calendar.list_events",
    "calendar.mark_date": "calendar.mark_date",
}

def _normalize_pending_payload(pending_payload: dict | None) -> Tuple[str | None, dict]:
    """
    Accepts legacy: {"tool":"browser", "url": "...", "actions":[...]}
    Or canonical:   {"name":"browser.screenshot", "args": {...}}
    Returns: (tool_name, args)
    """
    if not pending_payload:
        return None, {}
    if "name" in pending_payload and "args" in pending_payload:
        return pending_payload["name"], pending_payload.get("args") or {}
    if "tool" in pending_payload:
        legacy = dict(pending_payload)  # copy
        legacy_tool = legacy.pop("tool")
        name = TOOL_ALIASES.get(legacy_tool, legacy_tool)
        return name, legacy
    return None, {}

def create_run(
    db: Session,
    conversation_id: str,
    mode: str = "chat",
    plan: list[str] | None = None,
    needs_confirmation: Optional[bool] = None,
    pending_payload: dict | None = None
) -> Run:
    tool_name, args = _normalize_pending_payload(pending_payload)

    canonical_payload: dict | None = None
    if tool_name:
        # Validate against registry schema
        meta = require_valid(tool_name, args)
        # Inherit needs_confirmation from the registry if caller didn't specify
        if needs_confirmation is None:
            needs_confirmation = bool(meta.get("needs_confirmation"))
        canonical_payload = {"name": tool_name, "args": args}

    # Safe default if still None
    if needs_confirmation is None:
        needs_confirmation = False

    r = Run(
        conversation_id=conversation_id,
        status="running",
        mode=mode,
        needs_confirmation=needs_confirmation
    )
    r.plan = plan or []
    if canonical_payload:
        r.pending_payload = canonical_payload

    db.add(r)
    db.commit()
    db.refresh(r)
    return r

def add_step(db: Session, run_id: str, idx: int, kind: str, data: dict, status: str = "completed") -> Step:
    s = Step(run_id=run_id, idx=idx, kind=kind, status=status)
    s.data = data
    db.add(s); db.commit(); db.refresh(s)
    return s

def finish_run(db: Session, run_id: str, status: str = "completed") -> None:
    r = db.get(Run, run_id)
    if not r:
        return
    r.status = status
    r.finished_at = datetime.now(timezone.utc)
    db.commit()

def mark_awaiting_confirmation(db: Session, run_id: str):
    r = db.get(Run, run_id)
    if not r:
        return None
    r.status = "awaiting_confirmation"
    db.commit(); db.refresh(r)
    return r

def confirm_run(db: Session, run_id: str) -> Run | None:
    r = db.get(Run, run_id)
    if not r:
        return None
    if r.status != "awaiting_confirmation":
        return r
    r.status = "running"
    db.commit(); db.refresh(r)
    return r

def cancel_run(db: Session, run_id: str) -> bool:
    r = db.get(Run, run_id)
    if not r:
        return False
    r.status = "cancelled"
    r.finished_at = datetime.now(timezone.utc)
    db.commit()
    return True

def get_latest_pending(db: Session, conversation_id: str) -> Run | None:
    stmt = (
        select(Run)
        .where(Run.conversation_id == conversation_id, Run.status == "awaiting_confirmation")
        .order_by(desc(Run.started_at))
        .limit(1)
    )
    return db.scalars(stmt).first()
