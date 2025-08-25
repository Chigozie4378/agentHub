# app/tools/pdf/api.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.shared.http import ok, err
from app.shared.guard import guard_gate, bump_after_tool
from .service import generate_pdf

router = APIRouter(prefix="/tools/pdf", tags=["Tools: PDF"])

class PDFIn(BaseModel):
    html: str | None = None
    markdown: str | None = None
    filename: str | None = None

@router.post("/generate")
def api_pdf(inb: PDFIn, ctx=Depends(guard_gate("pdf"))):
    try:
        out = generate_pdf(html=inb.html, markdown=inb.markdown, filename=inb.filename)
        bump_after_tool(ctx, token_cost=2000)
        return ok(out)
    except ValueError as e:
        return err("invalid_pdf_input", code="invalid_input", status=400, details=str(e))
    except Exception as e:
        return err("tool_failed", status=500, details=str(e))
