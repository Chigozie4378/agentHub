from pydantic import BaseModel, EmailStr
from app.shared.artifacts import save_json

class EmailDraft(BaseModel):
    to: EmailStr
    subject: str
    body: str

def draft_email(to: str, subject: str, body: str) -> dict:
    draft = EmailDraft(to=to, subject=subject, body=body).model_dump()
    path = save_json("email-draft", draft)
    return {"status": "dry-run", "artifact_path": path, **draft}
