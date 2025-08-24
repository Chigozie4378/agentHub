# app/tools/search/service.py
from urllib.parse import urlencode

def web_search(q: str):
    if not q:
        return {"ok": False, "links": []}
    links = [
        f"https://www.google.com/search?{urlencode({'q': q})}",
        f"https://duckduckgo.com/?{urlencode({'q': q})}",
        f"https://www.bing.com/search?{urlencode({'q': q})}",
    ]
    return {"ok": True, "links": links}
