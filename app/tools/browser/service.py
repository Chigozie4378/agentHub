from typing import List, Dict, Any, Optional
from pathlib import Path
import os, sys, json, subprocess, shlex, tempfile

from app.shared.artifacts import save_bytes
from app.shared.config import settings

# Prefer Playwright when available
try:
    from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError  # type: ignore
    _HAS_PW = True
except Exception:
    _HAS_PW = False

def _ensure_selector_policy():
    """Force Selector policy (Windows only) so async subprocesses *can* work."""
    import asyncio
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass

# ---------- Chrome/Edge CLI fallback ----------

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
    else:  # linux
        cands += ["google-chrome", "chromium", "chromium-browser", "microsoft-edge"]
    return cands

def _find_browser_binary() -> Optional[str]:
    # 1) Explicit override from settings / env var
    if settings.CHROME_PATH:
        p = Path(settings.CHROME_PATH)
        if p.exists():
            return str(p)

    # 2) Fall back to existing candidate list
    for cand in _candidate_browsers():
        # absolute path
        if os.path.isabs(cand) and Path(cand).exists():
            return cand
        # on PATH
        from shutil import which
        w = which(cand)
        if w:
            return w

    # 3) Nothing found
    return None

def _cli_screenshot(url: str, width: int = 1366, height: int = 900) -> Dict[str, Any]:
    """
    Use Chrome/Edge CLI to take a full-page screenshot. No scrolling/actions —
    just load and capture, which is sufficient for Phase 2 demo + quotas.
    """
    bin_path = _find_browser_binary()
    if not bin_path:
        return {"ok": False, "error": "browser_not_found",
                "detail": "Chrome/Chromium/Edge not found. Set CHROME_PATH or install a browser."}

    # Temporary file; we’ll move the bytes into our artifact store
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    # Chrome flags: headless new mode, viewport, run compositor, disable GPU for servers
    args = [
        bin_path,
        "--headless=new",
        f"--window-size={width},{height}",
        "--hide-scrollbars",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        f"--screenshot={tmp_path}",
        url,
    ]
    try:
        # IMPORTANT: use subprocess.run (not asyncio). Works on all OSes.
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
        if proc.returncode != 0:
            return {"ok": False, "error": "browser_cli_failed",
                    "detail": proc.stderr.decode(errors="ignore")[:2000]}
        # read screenshot bytes and persist to artifacts dir
        data = Path(tmp_path).read_bytes()
        art_path = save_bytes("screenshot", "png", data)
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        return {"ok": True, "screenshot_path": art_path, "engine": "chrome-cli"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "browser_cli_timeout", "detail": "Timed out creating screenshot (45s)."}
    except Exception as e:
        return {"ok": False, "error": "browser_cli_exception", "detail": repr(e)}

# ---------- Playwright primary (when it works) ----------

async def _pw_browse(url: str, actions: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    _ensure_selector_policy()
    actions = actions or [{"type": "goto", "url": url}, {"type": "scroll", "y": 1200}]
    if not actions or actions[0].get("type") != "goto":
        actions = [{"type": "goto", "url": url}] + actions

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(viewport={"width": 1366, "height": 900}, ignore_https_errors=True)
        page = await context.new_page()

        step_errors: list[dict] = []
        for step in actions:
            try:
                t = step.get("type")
                if t == "goto":
                    await page.goto(step["url"], wait_until="domcontentloaded", timeout=30000)
                elif t == "click":
                    await page.click(step["selector"], timeout=15000)
                elif t == "scroll":
                    await page.mouse.wheel(0, int(step.get("y", 800)))
                elif t == "type":
                    await page.fill(step["selector"], step.get("text", ""), timeout=15000)
                else:
                    step_errors.append({"step": step, "error": "unknown_action"})
            except PWTimeoutError as e:
                step_errors.append({"step": step, "error": "timeout", "detail": str(e)})
            except Exception as e:
                step_errors.append({"step": step, "error": "exception", "detail": repr(e)})

        try:
            await page.wait_for_timeout(300)
        except Exception:
            pass

        png = await page.screenshot(full_page=True)
        art_path = save_bytes("screenshot", "png", png)
        await browser.close()

    return {"ok": True, "screenshot_path": art_path, "actions": actions, "engine": "playwright", "step_errors": step_errors}

# ---------- Public API used by the router ----------

async def browse(url: str, actions: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    # Force CLI on Windows unless you explicitly opt into Playwright
    engine = settings.BROWSER_ENGINE.lower()
    if engine == "cli" or sys.platform.startswith("win"):
        return _cli_screenshot(url)  # <- your existing CLI fallback

    if _HAS_PW and engine in ("auto", "playwright"):
        try:
            return await _pw_browse(url, actions)
        except Exception as e:
            out = _cli_screenshot(url)
            if out.get("ok"):
                out["note"] = f"Playwright failed: {repr(e)[:120]}"
            return out

    # No Playwright or engine=cli
    return _cli_screenshot(url)

