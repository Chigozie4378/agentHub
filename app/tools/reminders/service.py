from datetime import datetime
import uuid

_MEM: dict[str, list[dict]] = {}

def create_reminder(user_id: str, text: str, remind_at: str):
    r = {
        "id": uuid.uuid4().hex,
        "text": text,
        "remind_at": remind_at,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "status": "scheduled",
    }
    _MEM.setdefault(user_id, []).append(r)
    return r
