from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import os, sys, tempfile, subprocess
from pathlib import Path
import markdown as md

from app.shared.guard import guard_gate, bump_after_tool
from app.shared.artifacts import save_bytes

router = APIRouter(prefix="/tools/pdf", tags=["Tools: PDF"])

class PdfReq(BaseModel):
    html: Optional[str] = None
    markdown: Optional[str] = None
    filename: Optional[str] = "report"

# ---- small helpers (we keep local to avoid cross-module imports) ----
def _candidate_browsers() -> list[str]:
    env = os.getenv("CHROME_PATH") or os.getenv("BROWSER_PATH")
    if env:
        return [env]
    cands: list[str] = []
    if sys.platform.startswith("win"):
        local = os.getenv("LOCALAPPDATA", "")
        prog = os.getenv("PROGRAMFILES", "")
        progx = os.getenv("PROGRAMFILES(X86)", "")
        cands += [
            rf"{prog}\Google\Chrome\Application\chrome.exe",
            rf"{progx}\Google\Chrome\Application\chrome.exe",
            rf"{local}\Google\Chrome\Application\chrome.exe",
            rf"{prog}\Microsoft\Edge\Application\msedge.exe",
            rf"{progx}\Microsoft\Edge\Application\msedge.exe",
            rf"{local}\Microsoft\Edge\Application\msedge.exe",
        ]
    elif sys.platform == "darwin":
        cands += [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    else:
        cands += ["google-chrome", "chromium", "chromium-browser", "microsoft-edge"]
    return cands

def _find_browser_binary() -> Optional[str]:
    from shutil import which
    # env override handled in _candidate_browsers
    for cand in _candidate_browsers():
        if os.path.isabs(cand) and Path(cand).exists():
            return cand
        w = which(cand)
        if w:
            return w
    return None

def _render_html_to_pdf_via_chrome(html: str, out_name: str) -> dict:
    bin_path = _find_browser_binary()
    if not bin_path:
        return {"ok": False, "error": "browser_not_found",
                "detail": "Chrome/Chromium/Edge not found. Set CHROME_PATH or install a browser."}

    # write a temp HTML file
    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = Path(tmpdir) / "doc.html"
        pdf_tmp = Path(tmpdir) / "out.pdf"
        html_path.write_text(html, encoding="utf-8")

        # Build args. virtual-time-budget helps load some JS-powered pages.
        args = [
            bin_path,
            "--headless=new",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            f"--print-to-pdf={pdf_tmp.as_posix()}",
            f"--virtual-time-budget=4000",
            html_path.as_uri(),  # file:///... URL
        ]
        try:
            proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            if proc.returncode != 0 or not pdf_tmp.exists():
                return {"ok": False, "error": "chrome_print_failed", "detail": proc.stderr.decode(errors="ignore")[:2000]}
            pdf_bytes = pdf_tmp.read_bytes()
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "chrome_print_timeout", "detail": "Timed out generating PDF"}
        except Exception as e:
            return {"ok": False, "error": "chrome_print_exception", "detail": repr(e)}

    # Persist to your artifact store
    path = save_bytes(out_name or "report", "pdf", pdf_bytes)
    return {"ok": True, "pdf_path": path, "engine": "chrome-cli"}

# ---- API ----
@router.post("/generate", summary="Generate a PDF from HTML or Markdown")
def api_pdf(req: PdfReq, ctx = Depends(guard_gate("pdf"))):
    if not (req.html or req.markdown):
        raise HTTPException(400, "Provide 'html' or 'markdown'")

    html = req.html or md.markdown(req.markdown or "")
    out = _render_html_to_pdf_via_chrome(html, req.filename or "report")
    if out.get("ok"):
        bump_after_tool(ctx, token_cost=2500)
    return out
