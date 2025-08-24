# app/tools/places/service.py
from urllib.parse import urlencode

def search_places(q: str, near: str | None = None):
    query = q if not near else f"{q} near {near}"
    # return useful links (no API key needed)
    links = [
        f"https://www.google.com/maps/search/{urlencode({'': query})[1:]}",
        f"https://www.google.com/search?{urlencode({'q': query})}",
        f"https://duckduckgo.com/?{urlencode({'q': query})}",
    ]
    return {"ok": True, "query": query, "links": links}
