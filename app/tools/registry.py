from typing import TypedDict, Callable, Any

class ToolMeta(TypedDict, total=False):
    name: str
    summary: str
    doc_url: str
    needs_confirmation: bool
    guard_feature: str          # key used by guard_gate
    input_schema: dict          # JSON schema for payload
    returns: str

REGISTRY: list[ToolMeta] = [
    {
        "name": "browser.screenshot",
        "summary": "Open a URL, optional actions (click/type/scroll/wait), return screenshot artifact.",
        "doc_url": "/docs#/Tools:%20Browser/api_browse_tools_browser_post",
        "needs_confirmation": True,
        "guard_feature": "browser",
        "input_schema": {
            "type":"object",
            "properties":{
                "url":{"type":"string","format":"uri"},
                "actions":{"type":"array","items":{"type":"object"}}
            },
            "required":["url"]
        },
        "returns":"{ ok:boolean, screenshot_path:string, step_errors?:[] }"
    },
    {
        "name": "pdf.generate",
        "summary": "Render HTML/Markdown into a PDF and store as artifact.",
        "doc_url": "/docs#/Tools:%20PDF/api_pdf_tools_pdf_generate_post",
        "needs_confirmation": False,
        "guard_feature": "pdf",
        "input_schema": {"type":"object","properties":{"html":{"type":"string"},"markdown":{"type":"string"},"filename":{"type":"string"}}, "oneOf":[{"required":["html"]},{"required":["markdown"]}]},
        "returns":"{ ok:boolean, pdf_path:string }"
    },
    {
        "name": "csv.preview",
        "summary": "Parse a CSV (uploaded file id) and return headers + first N rows; also stores normalized CSV.",
        "doc_url": "/docs#/Tools:%20CSV/api_csv_preview_tools_csv_preview_post",
        "needs_confirmation": False,
        "guard_feature": "csv",
        "input_schema": {"type":"object","properties":{"file_id":{"type":"string"},"limit":{"type":"integer"}}, "required":["file_id"]},
        "returns":"{ ok:boolean, headers:string[], rows:any[][], normalized_csv_path:string }"
    },
    {
        "name": "places.search",
        "summary": "Dry-run: build a query URL for nearby restaurants/businesses (no external API key required).",
        "doc_url": "/docs#/Tools:%20Places/api_places_search_tools_places_search_post",
        "needs_confirmation": True,
        "guard_feature": "places",
        "input_schema": {"type":"object","properties":{"q":{"type":"string"},"near":{"type":"string"}},"required":["q"]},
        "returns":"{ ok:boolean, query:string, links:string[] }"
    }
]
