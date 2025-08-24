from fastapi import APIRouter
from pydantic import BaseModel
from .service import generate_pdf

router = APIRouter(prefix="/tools/pdf", tags=["Tools: PDF"])

class PdfIn(BaseModel):
    html: str | None = None
    markdown: str | None = None
    filename: str | None = None

@router.post("/generate")
def api_pdf(inb: PdfIn):
    out = generate_pdf(html=inb.html, markdown=inb.markdown, filename=inb.filename)
    return out
