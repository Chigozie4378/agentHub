# app/tools/calendar/service.py
from datetime import datetime
import uuid

_MEM: dict[str, list[dict]] = {}

def create_event(user_id: str, title: str, start: str, end: str, location: str | None = None):
    e = {
        "id": uuid.uuid4().hex,
        "title": title,
        "start": start,
        "end": end,
        "location": location,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    _MEM.setdefault(user_id, []).append(e)
    return e

def update_event(user_id: str, event_id: str, **kwargs):
    for e in _MEM.get(user_id, []):
        if e["id"] == event_id:
            e.update({k:v for k,v in kwargs.items() if v is not None})
            return e
    raise KeyError("event not found")

def delete_event(user_id: str, event_id: str):
    arr = _MEM.get(user_id, [])
    before = len(arr)
    _MEM[user_id] = [e for e in arr if e["id"] != event_id]
    return len(_MEM[user_id]) < before

def list_events(user_id: str, start: str | None = None, end: str | None = None):
    # demo: no real filtering unless both provided
    items = list(_MEM.get(user_id, []))
    return items

def mark_date(user_id: str, date: str, label: str):
    e = {
        "id": uuid.uuid4().hex,
        "title": label,
        "start": date,
        "end": date,
        "location": None,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    _MEM.setdefault(user_id, []).append(e)
    return {"date": date, "label": label}
