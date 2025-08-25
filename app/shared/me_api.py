# app/shared/me_api.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.shared.db import get_db
from app.shared.guard import _read_usage          # reuse the guard’s usage reader
from app.shared.config import settings
from app.shared.auth import get_user              # <— use real auth (demo/JWT toggle lives here)

router = APIRouter(prefix="/me", tags=["Me"])

@router.get("/limits")
def my_limits(user = Depends(get_user), db: Session = Depends(get_db)):
    uid  = user["sub"]
    tier = user.get("tier", settings.DEFAULT_TIER)

    usage = _read_usage(db, uid)

    if tier == "paid":
        max_tasks, max_tokens = settings.PAID_TASK_LIMIT, settings.PAID_TOKEN_BUDGET
    elif tier == "dev":
        max_tasks, max_tokens = 10**9, 10**12
    else:
        max_tasks, max_tokens = settings.FREE_TASK_LIMIT, settings.FREE_TOKEN_BUDGET

    return {
        "user": {"sub": uid, "tier": tier, "role": user.get("role"), "mode": user.get("mode")},
        "tasks_used": usage["tasks"],
        "tasks_limit": max_tasks,
        "tokens_used": usage["tokens"],
        "tokens_limit": max_tokens,
    }
