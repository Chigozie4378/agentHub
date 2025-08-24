
from typing import Optional, Literal
from datetime import datetime
import uuid

_MEM: dict[str, list[dict]] = {}  # user_id -> items

def create_todo(user_id: str, title: str, due_at: Optional[str] = None, labels: list[str] | None = None):
    item = {
        "id": uuid.uuid4().hex,
        "title": title,
        "status": "pending",
        "labels": labels or [],
        "due_at": due_at,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    _MEM.setdefault(user_id, []).append(item)
    return item

def list_todos(user_id: str, status: Optional[Literal["pending","completed"]] = None):
    items = _MEM.get(user_id, [])
    if status:
        items = [i for i in items if i["status"] == status]
    return items

def update_todo(user_id: str, todo_id: str, status: Optional[str] = None):
    for i in _MEM.get(user_id, []):
        if i["id"] == todo_id:
            if status: i["status"] = status
            return i
    raise KeyError("todo not found")

def delete_todo(user_id: str, todo_id: str):
    arr = _MEM.get(user_id, [])
    before = len(arr)
    _MEM[user_id] = [i for i in arr if i["id"] != todo_id]
    return len(_MEM[user_id]) < before
