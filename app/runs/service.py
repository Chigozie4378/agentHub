from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.runs.models import Run, Step
from datetime import datetime, timezone

def create_run(db: Session, conversation_id: str, mode: str = "chat", plan: list[str] | None = None, needs_confirmation: bool = False, pending_payload: dict | None = None) -> Run:
    r = Run(conversation_id=conversation_id, status="running", mode=mode, needs_confirmation=needs_confirmation)
    r.plan = plan or []
    if pending_payload: r.pending_payload = pending_payload
    db.add(r); db.commit(); db.refresh(r)
    return r

def add_step(db: Session, run_id: str, idx: int, kind: str, data: dict, status: str = "completed") -> Step:
    s = Step(run_id=run_id, idx=idx, kind=kind, status=status); s.data = data
    db.add(s); db.commit(); db.refresh(s)
    return s

def finish_run(db: Session, run_id: str, status: str = "completed") -> None:
    r = db.get(Run, run_id)
    if not r: return
    r.status = status; r.finished_at = datetime.now(timezone.utc)
    db.commit()

# NEW: move run into awaiting_confirmation
def mark_awaiting_confirmation(db: Session, run_id: str):
    r = db.get(Run, run_id)
    if not r: return None
    r.status = "awaiting_confirmation"
    db.commit(); db.refresh(r)
    return r

# NEW: confirm/cancel a pending run
def confirm_run(db: Session, run_id: str) -> Run | None:
    r = db.get(Run, run_id)
    if not r: return None
    if r.status != "awaiting_confirmation": return r
    r.status = "running"
    db.commit(); db.refresh(r)
    return r

def cancel_run(db: Session, run_id: str) -> bool:
    r = db.get(Run, run_id)
    if not r: return False
    r.status = "cancelled"; r.finished_at = datetime.now(timezone.utc)
    db.commit(); return True

# NEW: fetch latest pending run for a conversation
def get_latest_pending(db: Session, conversation_id: str) -> Run | None:
    stmt = select(Run).where(Run.conversation_id == conversation_id, Run.status == "awaiting_confirmation").order_by(desc(Run.started_at)).limit(1)
    return db.scalars(stmt).first()
