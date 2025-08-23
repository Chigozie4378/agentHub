from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from app.shared.db import get_db
from .service import draft_email

router = APIRouter(prefix="/tools/email", tags=["Tools: Email"])

class EmailReq(BaseModel):
    to: EmailStr
    subject: str
    body: str

@router.post("/send", summary="Create a dry-run email draft (no send)")
def api_email_send(body: EmailReq, db=Depends(get_db)):
    return draft_email(body.to, body.subject, body.body)
