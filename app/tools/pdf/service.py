
from pathlib import Path
from typing import Optional
import uuid

ARTIFACTS = Path("storage/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

def generate_pdf(html: Optional[str] = None, markdown: Optional[str] = None, filename: Optional[str] = None):
    """
    Minimal demo. If WeasyPrint is installed, use it. Otherwise, save HTML fallback.
    """
    if not html and markdown:
        # tiny markdown -> html fallback (very naive)
        html = f"<html><body><pre>{markdown}</pre></body></html>"
    if not html:
        raise ValueError("generate_pdf requires html or markdown")

    out_name = filename or f"doc_{uuid.uuid4().hex}.pdf"
    out_path = ARTIFACTS / out_name

    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(str(out_path))
        return {"ok": True, "pdf_path": str(out_path)}
    except Exception:
        # fallback: write .html so demo still produces an artifact
        html_name = out_name.replace(".pdf", ".html")
        html_path = ARTIFACTS / html_name
        html_path.write_text(html, encoding="utf-8")
        return {
            "ok": False,
            "pdf_path": None,
            "fallback_html_path": str(html_path),
            "message": "WeasyPrint missing; saved HTML fallback."
        }
