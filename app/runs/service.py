from sqlalchemy.orm import Session
from sqlalchemy import select
from app.runs.models import Run, Step

def create_run(db: Session, conversation_id: str, mode: str = "chat", plan: list[str] | None = None) -> Run:
    r = Run(conversation_id=conversation_id, status="running", mode=mode)
    r.plan = plan or []
    db.add(r)
    db.commit()
    db.refresh(r)
    return r

def add_step(db: Session, run_id: str, idx: int, kind: str, data: dict, status: str = "completed") -> Step:
    s = Step(run_id=run_id, idx=idx, kind=kind, status=status)
    s.data = data
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

def finish_run(db: Session, run_id: str, status: str = "completed") -> None:
    r = db.get(Run, run_id)
    if not r:
        return
    from datetime import datetime, timezone
    r.status = status
    r.finished_at = datetime.now(timezone.utc)
    db.commit()
