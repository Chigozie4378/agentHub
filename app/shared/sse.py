import asyncio, json
from typing import AsyncIterator, Dict, Set

# conversation_id -> set of subscriber queues
_SUBS: Dict[str, Set[asyncio.Queue]] = {}

def _get_room(cid: str) -> Set[asyncio.Queue]:
    return _SUBS.setdefault(cid, set())

async def publish(cid: str, event: str, data: dict):
    msg = (event, data)
    for q in list(_get_room(cid)):
        try:
            q.put_nowait(msg)
        except asyncio.QueueFull:
            pass

async def subscribe(cid: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _get_room(cid).add(q)
    return q

def unsubscribe(cid: str, q: asyncio.Queue):
    _get_room(cid).discard(q)

async def sse_stream(cid: str) -> AsyncIterator[bytes]:
    """
    Yields Server-Sent Events for the given conversation.
    """
    q = await subscribe(cid)
    try:
        # initial ping (optional)
        yield b": connected\n\n"
        while True:
            event, data = await q.get()
            payload = f"event: {event}\n" + f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            yield payload.encode("utf-8")
    except asyncio.CancelledError:
        # client disconnected
        pass
    finally:
        unsubscribe(cid, q)
