from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.shared.db import get_db
from app.runs.service import confirm_run, cancel_run
from app.runs.models import Run
from app.shared import sse


from sqlalchemy import select, desc
from app.runs.models import Run, Step

router = APIRouter(prefix="/runs", tags=["Runs"])

def current_user_id() -> str:  # stub for now
    return "demo-user"

@router.post("/{run_id}/confirm")
async def api_confirm_run(run_id: str, db: Session = Depends(get_db)):
    r = confirm_run(db, run_id)
    if not r: raise HTTPException(404, "Run not found")
    # let stream know we've been confirmed
    await sse.publish(r.conversation_id, "confirmation", {"run_id": r.id, "status": "confirmed"})
    return {"ok": True, "run_id": r.id, "status": r.status}

@router.post("/{run_id}/cancel")
async def api_cancel_run(run_id: str, db: Session = Depends(get_db)):
    ok = cancel_run(db, run_id)
    if not ok: raise HTTPException(404, "Run not found")
    # Inform stream
    # (we don't have the conversation id without loading; load again quickly)
    from app.runs.models import Run
    r = db.get(Run, run_id)
    if r:
        await sse.publish(r.conversation_id, "confirmation", {"run_id": run_id, "status": "cancelled"})
    return {"ok": True, "run_id": run_id, "status": "cancelled"}


@router.get("/by-conversation/{conversation_id}")
def runs_for_conversation(conversation_id: str, db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Run).where(Run.conversation_id==conversation_id).order_by(desc(Run.started_at)).limit(20)
    ).all()
    return [
        {
            "id": r.id,
            "status": r.status,
            "mode": r.mode,
            "plan": r.plan,
            "started_at": r.started_at,
            "finished_at": r.finished_at
        } for r in rows
    ]
