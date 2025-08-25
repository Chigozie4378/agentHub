# app/tools/email/api.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from app.shared.http import ok, err
from app.shared.guard import guard_gate, bump_after_tool
from .service import draft_email

router = APIRouter(prefix="/tools/email", tags=["Tools: Email"])

class EmailIn(BaseModel):
    to: EmailStr
    subject: str
    body: str
    dry_run: bool = True

@router.post("/draft_send")
def api_email(inb: EmailIn, ctx=Depends(guard_gate("email"))):
    try:
        out = draft_email(inb.to, inb.subject, inb.body, dry_run=inb.dry_run)
        bump_after_tool(ctx, token_cost=3000)
        return ok(out)
    except ValueError as e:
        return err("invalid_email", status=400, details=str(e))
    except Exception as e:
        return err("tool_failed", status=500, details=str(e))
