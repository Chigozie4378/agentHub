from typing import TypedDict

class ToolMeta(TypedDict, total=False):
    name: str
    summary: str
    doc_url: str          # points to Swagger op
    needs_confirmation: bool
    guard_feature: str    # used by guard_gate("<feature>")
    input_schema: dict    # JSON Schema for request body
    returns: str          # short doc-string of the response shape

REGISTRY: list[ToolMeta] = [
    # -------- Web / Browser ----------
    {
        "name": "browser.screenshot",
        "summary": "Open a URL, optional actions (goto/click/type/scroll/wait), return screenshot artifact.",
        "doc_url": "/docs#/Tools:%20Browser/api_browse_tools_browser_post",
        "needs_confirmation": False,  # read-only by default
        "guard_feature": "browser",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "format": "uri"},
                "actions": {"type": "array", "items": {"type": "object"}}
            },
            "required": ["url"]
        },
        "returns": "{ ok:boolean, engine:'playwright|chrome-cli', screenshot_path:string, step_errors?:[] }"
    },

    # -------- Email ----------
    {
        "name": "email.draft_send",
        "summary": "Compose an email and send (dry-run by default).",
        "doc_url": "/docs#/Tools:%20Email/api_tools_email_post",
        "needs_confirmation": True,  # sending content to external party
        "guard_feature": "email",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "dry_run": {"type": "boolean", "default": True}
            },
            "required": ["to", "subject", "body"]
        },
        "returns": "{ ok:boolean, status:'dry-run|sent', artifact_path?:string }"
    },

    # -------- PDF ----------
    {
        "name": "pdf.generate",
        "summary": "Render HTML/Markdown into a PDF and store as artifact.",
        "doc_url": "/docs#/Tools:%20PDF/api_pdf_tools_pdf_generate_post",
        "needs_confirmation": False,
        "guard_feature": "pdf",
        "input_schema": {
            "type": "object",
            "properties": {
                "html": {"type": "string"},
                "markdown": {"type": "string"},
                "filename": {"type": "string"}
            },
            "oneOf": [{"required": ["html"]}, {"required": ["markdown"]}]
        },
        "returns": "{ ok:boolean, pdf_path:string, engine:'chrome-cli' }"
    },

    # -------- CSV ----------
    {
        "name": "csv.preview",
        "summary": "Parse CSV (uploaded file_id) and return headers + first rows; also stores normalized CSV.",
        "doc_url": "/docs#/Tools:%20CSV/api_csv_preview_tools_csv_preview_post",
        "needs_confirmation": False,
        "guard_feature": "csv",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_id": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200}
            },
            "required": ["file_id"]
        },
        "returns": "{ ok:boolean, headers:string[], rows:any[][], normalized_csv_path:string }"
    },

    # -------- Places / Navigation (dry-run links) ----------
    {
        "name": "places.search",
        "summary": "Build query URLs for nearby restaurants/businesses (no API key required).",
        "doc_url": "/docs#/Tools:%20Places/api_places_search_tools_places_search_post",
        "needs_confirmation": False,
        "guard_feature": "places",
        "input_schema": {
            "type": "object",
            "properties": {
                "q": {"type": "string"},
                "near": {"type": "string"}
            },
            "required": ["q"]
        },
        "returns": "{ ok:boolean, query:string, links:string[] }"
    },

    # -------- Search (web) ----------
    {
        "name": "search.web",
        "summary": "General-purpose search: returns search engine links (add SerpAPI later).",
        "doc_url": "/docs#/Tools:%20Search/search_web_tools_search_web_post",
        "needs_confirmation": False,
        "guard_feature": "search",
        "input_schema": {
            "type": "object",
            "properties": { "q": {"type": "string"} },
            "required": ["q"]
        },
        "returns": "{ ok:boolean, links:string[] }"
    },

    # -------- Download ----------
    {
        "name": "download.fetch",
        "summary": "Download a file from the internet and store as artifact.",
        "doc_url": "/docs#/Tools:%20Download/download_file_tools_download_post",
        "needs_confirmation": False,
        "guard_feature": "download",
        "input_schema": {
            "type": "object",
            "properties": { "url": {"type": "string", "format": "uri"} },
            "required": ["url"]
        },
        "returns": "{ ok:boolean, artifact_path:string, size:number }"
    },

    # -------- Summarize (non-LLM baseline) ----------
    {
        "name": "summarize.document",
        "summary": "Summarize a document (baseline heuristic; swap to LLM later).",
        "doc_url": "/docs#/Tools:%20Summarize/summarize_tools_summarize_post",
        "needs_confirmation": False,
        "guard_feature": "summarize",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_id": {"type": "string"},
                "max_chars": {"type": "integer", "default": 800}
            },
            "required": ["file_id"]
        },
        "returns": "{ ok:boolean, summary:string, length:number }"
    },

    # -------- Sentiment ----------
    {
        "name": "sentiment.analyze",
        "summary": "Analyze sentiment using VADER (baseline).",
        "doc_url": "/docs#/Tools:%20Sentiment/analyze_sentiment_tools_sentiment_post",
        "needs_confirmation": False,
        "guard_feature": "sentiment",
        "input_schema": {
            "type": "object",
            "properties": { "text": {"type": "string"} },
            "required": ["text"]
        },
        "returns": "{ ok:boolean, label:'positive|neutral|negative', scores:object }"
    },

    # -------- Todos ----------
    {
        "name": "todos.create",
        "summary": "Add item to todo list.",
        "doc_url": "/docs#/Tools:%20Todos/create_todo_tools_todos_post",
        "needs_confirmation": False,
        "guard_feature": "todos",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "due_at": {"type": "string", "format": "date-time"},
                "labels": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["title"]
        },
        "returns": "{ ok:boolean, id:string, item:TodoItem }"
    },
    {
        "name": "todos.list",
        "summary": "List todo items (pending/completed).",
        "doc_url": "/docs#/Tools:%20Todos/list_todos_tools_todos_get",
        "needs_confirmation": False,
        "guard_feature": "todos",
        "input_schema": { "type": "object", "properties": { "status": {"type": "string"} } },
        "returns": "{ ok:boolean, items:TodoItem[] }"
    },
    {
        "name": "todos.update",
        "summary": "Mark complete or update a todo.",
        "doc_url": "/docs#/Tools:%20Todos/update_todo_tools_todos__todo_id__patch",
        "needs_confirmation": False,
        "guard_feature": "todos",
        "input_schema": {
            "type": "object",
            "properties": {
                "todo_id": {"type": "string"},
                "status": {"type": "string", "enum": ["pending","completed"]}
            },
            "required": ["todo_id"]
        },
        "returns": "{ ok:boolean, item:TodoItem }"
    },
    {
        "name": "todos.delete",
        "summary": "Delete a todo item.",
        "doc_url": "/docs#/Tools:%20Todos/delete_todo_tools_todos__todo_id__delete",
        "needs_confirmation": False,
        "guard_feature": "todos",
        "input_schema": {
            "type": "object",
            "properties": { "todo_id": {"type": "string"} },
            "required": ["todo_id"]
        },
        "returns": "{ ok:boolean }"
    },

    # -------- Notes ----------
    {
        "name": "notes.create",
        "summary": "Create a note.",
        "doc_url": "/docs#/Tools:%20Notes/create_note_tools_notes_post",
        "needs_confirmation": False,
        "guard_feature": "notes",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["text"]
        },
        "returns": "{ ok:boolean, id:string, item:NoteItem }"
    },
    {
        "name": "notes.summarize",
        "summary": "Summarize notes (baseline; later LLM).",
        "doc_url": "/docs#/Tools:%20Notes/summarize_notes_tools_notes_summarize_post",
        "needs_confirmation": False,
        "guard_feature": "notes",
        "input_schema": {
            "type": "object",
            "properties": {
                "tag": {"type": "string"},
                "since": {"type": "string", "format": "date"}
            }
        },
        "returns": "{ ok:boolean, summary:string, count:number }"
    },

    # -------- Reminders ----------
    {
        "name": "reminders.create",
        "summary": "Create a reminder.",
        "doc_url": "/docs#/Tools:%20Reminders/create_reminder_tools_reminders_post",
        "needs_confirmation": False,
        "guard_feature": "reminders",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "remind_at": {"type": "string", "format": "date-time"}
            },
            "required": ["text", "remind_at"]
        },
        "returns": "{ ok:boolean, id:string, item:ReminderItem }"
    },

    # -------- Calendar ----------
    {
        "name": "calendar.create_event",
        "summary": "Create a calendar event.",
        "doc_url": "/docs#/Tools:%20Calendar/create_event_tools_calendar_events_post",
        "needs_confirmation": False,
        "guard_feature": "calendar",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "start": {"type": "string", "format": "date-time"},
                "end": {"type": "string", "format": "date-time"},
                "location": {"type": "string"},
                "attendees": {"type": "array", "items": {"type": "string", "format": "email"}}
            },
            "required": ["title", "start"]
        },
        "returns": "{ ok:boolean, id:string, item:EventItem }"
    },
    {
        "name": "calendar.update_event",
        "summary": "Reschedule/update an event.",
        "doc_url": "/docs#/Tools:%20Calendar/reschedule_event_tools_calendar_events__event_id__patch",
        "needs_confirmation": False,
        "guard_feature": "calendar",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "start": {"type": "string", "format": "date-time"},
                "end": {"type": "string", "format": "date-time"},
                "location": {"type": "string"},
                "attendees": {"type": "array", "items": {"type": "string", "format": "email"}}
            },
            "required": ["event_id"]
        },
        "returns": "{ ok:boolean, item:EventItem }"
    },
    {
        "name": "calendar.delete_event",
        "summary": "Delete an event.",
        "doc_url": "/docs#/Tools:%20Calendar/delete_event_tools_calendar_events__event_id__delete",
        "needs_confirmation": False,
        "guard_feature": "calendar",
        "input_schema": {
            "type": "object",
            "properties": { "event_id": {"type": "string"} },
            "required": ["event_id"]
        },
        "returns": "{ ok:boolean }"
    },
    {
        "name": "calendar.list_events",
        "summary": "List events (optional time window).",
        "doc_url": "/docs#/Tools:%20Calendar/list_events_tools_calendar_events_get",
        "needs_confirmation": False,
        "guard_feature": "calendar",
        "input_schema": {
            "type": "object",
            "properties": {
                "start": {"type": "string", "format": "date-time"},
                "end": {"type": "string", "format": "date-time"}
            }
        },
        "returns": "{ ok:boolean, items:EventItem[] }"
    },
    {
        "name": "calendar.mark_date",
        "summary": "Flag a specific date (holiday/milestone).",
        "doc_url": "/docs#/Tools:%20Calendar/mark_date_tools_calendar_mark_date_post",
        "needs_confirmation": False,
        "guard_feature": "calendar",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "format": "date"},
                "label": {"type": "string"}
            },
            "required": ["date", "label"]
        },
        "returns": "{ ok:boolean, marked:{date,label} }"
    }
]
