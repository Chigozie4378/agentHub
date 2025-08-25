import json, hashlib, datetime as dt
from fastapi import Header, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.shared.db import get_db
from app.shared.models import Base
from sqlalchemy import Column, String, Text, DateTime

class IdemRecord(Base):
    __tablename__ = "idempotency_keys"
    key = Column(String(128), primary_key=True)
    request_sig = Column(String(64), nullable=False)
    response_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

def _sig(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()

async def require_idem(
    db: Session = Depends(get_db),
    idem_key: str | None = Header(default=None, alias="Idempotency-Key"),
    payload: dict | None = None,  # you will pass this explicitly from the route
):
    if not idem_key:
        return {"idem": None}  # not provided -> not enforced
    sig = _sig(payload or {})
    rec = db.get(IdemRecord, idem_key)
    if rec and rec.request_sig == sig:
        # short-circuit with cached response
        from fastapi import HTTPException
        raise HTTPException(status_code=200, detail=json.loads(rec.response_json))
    return {"idem": {"key": idem_key, "sig": sig}}

def save_idem(db: Session, idem_ctx: dict | None, response_obj: dict):
    if not idem_ctx or not idem_ctx.get("key"): 
        return
    rec = IdemRecord(key=idem_ctx["key"], request_sig=idem_ctx["sig"], response_json=json.dumps(response_obj))
    db.add(rec); db.commit()
