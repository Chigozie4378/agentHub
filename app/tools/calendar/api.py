from fastapi import APIRouter, Path, Query
from pydantic import BaseModel
from .service import create_event, update_event, delete_event, list_events, mark_date

router = APIRouter(prefix="/tools/calendar", tags=["Tools: Calendar"])

def current_user_id() -> str:
    return "demo-user"

class EventCreateIn(BaseModel):
    title: str
    start: str
    end: str
    location: str | None = None

@router.post("/events")
def api_events_create(inb: EventCreateIn):
    return create_event(current_user_id(), inb.title, inb.start, inb.end, inb.location)

class EventUpdateIn(BaseModel):
    title: str | None = None
    start: str | None = None
    end: str | None = None
    location: str | None = None

@router.patch("/events/{event_id}")
def api_events_update(event_id: str = Path(...), inb: EventUpdateIn | None = None):
    data = inb.dict(exclude_unset=True) if inb else {}
    return update_event(current_user_id(), event_id, **data)

@router.delete("/events/{event_id}")
def api_events_delete(event_id: str = Path(...)):
    return {"ok": delete_event(current_user_id(), event_id)}

@router.get("/events")
def api_events_list():
    return list_events(current_user_id())

class MarkDateIn(BaseModel):
    date: str
    label: str

@router.post("/mark_date")
def api_mark_date(inb: MarkDateIn):
    return mark_date(current_user_id(), inb.date, inb.label)
