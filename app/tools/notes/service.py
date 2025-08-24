
from datetime import datetime
import uuid

_MEM: dict[str, list[dict]] = {}  # user_id -> notes

def create_note(user_id: str, text: str, tags: list[str] | None = None):
    n = {
        "id": uuid.uuid4().hex,
        "text": text,
        "tags": tags or [],
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    _MEM.setdefault(user_id, []).append(n)
    return n

def summarize_notes(user_id: str, tag: str | None = None, since: str | None = None):
    items = _MEM.get(user_id, [])
    if tag:
        items = [n for n in items if tag in n.get("tags", [])]
    # demo “summary”: concat first 3 trimmed texts
    texts = [n["text"][:100] for n in items[:3]]
    return {"summary": " | ".join(texts), "count": len(items)}
