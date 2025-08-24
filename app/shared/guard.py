import time
from datetime import datetime
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.shared.db import get_db
from app.shared.config import settings

# stubbed auth -> always "demo-user" with DEFAULT_TIER
def current_user():
    return {"sub": "demo-user", "tier": settings.DEFAULT_TIER, "role": "user"}

def _today():
    return datetime.utcnow().strftime("%Y%m%d")

def _read_usage(db: Session, user_id: str):
    day = _today()
    row = db.execute(
        text("SELECT tasks, tokens FROM user_usage WHERE user_id=:u AND day=:d"),
        {"u": user_id, "d": day}
    ).first()
    return {"tasks": row[0], "tokens": row[1]} if row else {"tasks": 0, "tokens": 0}

def _bump_usage(db: Session, user_id: str, tasks_inc=0, tokens_inc=0):
    day = _today()
    row = db.execute(text("SELECT id, tasks, tokens FROM user_usage WHERE user_id=:u AND day=:d"),
                     {"u": user_id, "d": day}).first()
    if row:
        db.execute(text("UPDATE user_usage SET tasks=tasks+:t, tokens=tokens+:k WHERE id=:id"),
                   {"t": tasks_inc, "k": tokens_inc, "id": row[0]})
    else:
        db.execute(text("INSERT INTO user_usage(user_id, day, tasks, tokens) VALUES (:u,:d,:t,:k)"),
                   {"u": user_id, "d": day, "t": tasks_inc, "k": tokens_inc})
    db.commit()

def guard_gate(feature: str, requires_confirmation: bool = True):
    """
    Use as a FastAPI dependency on tool endpoints.
    Enforces per-tier quotas and, optionally, confirmation requirement (we only enforce
    confirmation at the chat level; this guard just blocks if over quota).
    """
    def _dep(user=Depends(current_user), db: Session = Depends(get_db)):
        uid = user["sub"]; tier = user.get("tier", settings.DEFAULT_TIER)
        usage = _read_usage(db, uid)
        if tier == "paid":
            max_tasks, max_tokens = settings.PAID_TASK_LIMIT, settings.PAID_TOKEN_BUDGET
        elif tier == "dev":
            max_tasks, max_tokens = 10**9, 10**12
        else:
            max_tasks, max_tokens = settings.FREE_TASK_LIMIT, settings.FREE_TOKEN_BUDGET

        if usage["tasks"] >= max_tasks:
            raise HTTPException(402, f"Quota exceeded: tasks {usage['tasks']}/{max_tasks}")
        if usage["tokens"] >= max_tokens:
            raise HTTPException(402, f"Quota exceeded: tokens {usage['tokens']}/{max_tokens}")

        # return a tiny context so routes can bump usage after success
        return {"user": user, "db": db, "usage": usage, "max": {"tasks": max_tasks, "tokens": max_tokens}}
    return _dep

def bump_after_tool(ctx, token_cost: int = 5000):
    _bump_usage(ctx["db"], ctx["user"]["sub"], tasks_inc=1, tokens_inc=token_cost)

def bump_for_user(db: Session, user_id: str, token_cost: int = 5000, tasks_inc: int = 1):
    _bump_usage(db, user_id, tasks_inc=tasks_inc, tokens_inc=token_cost)

