import asyncio
from typing import List, Dict, Any
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
from app.shared.artifacts import save_bytes

ACTIONS_SCHEMA = """
actions: list of steps. Each step is one of:
  {"type":"goto","url":"https://..."}
  {"type":"click","selector":"text=Sign in"} or {"type":"click","selector":"#submit"}
  {"type":"scroll","y":1200}
  {"type":"type","selector":"input[name=q]","text":"hello"}
"""

async def browse(url: str, actions: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    actions = actions or [{"type":"goto","url":url},{"type":"scroll","y":1200}]
    # Ensure first step is a goto
    if not actions or actions[0].get("type") != "goto":
        actions = [{"type":"goto","url":url}] + actions

    try:
        async with async_playwright() as p:
            # Safer launch flags work across Windows/Linux/macOS
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"]
            )
            context = await browser.new_context(
                viewport={"width": 1366, "height": 900},
                ignore_https_errors=True  # tolerate cert hiccups
            )
            page = await context.new_page()

            # Run steps
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
                        await page.fill(step["selector"], step.get("text",""), timeout=15000)
                    else:
                        step_errors.append({"step": step, "error": "unknown_action"})
                except PWTimeoutError as e:
                    step_errors.append({"step": step, "error": "timeout", "detail": str(e)})
                except Exception as e:
                    step_errors.append({"step": step, "error": "exception", "detail": repr(e)})

            # Best-effort wait before screenshot
            try:
                await page.wait_for_timeout(500)  # small settle
            except Exception:
                pass

            png = await page.screenshot(full_page=True)
            path = save_bytes("screenshot", "png", png)
            await browser.close()

        return {
            "ok": True,
            "screenshot_path": path,
            "actions": actions,
            "step_errors": step_errors,
            "note": "screenshot saved"
        }

    except Exception as e:
        # Surface rich diagnostics to the caller
        return {
            "ok": False,
            "error": "browse_failed",
            "detail": repr(e),
            "hint": "Ensure 'python -m playwright install chromium' succeeded and the server can reach the URL."
        }
