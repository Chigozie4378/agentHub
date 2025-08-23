def extract_text_file(path: str, max_chars: int = 40_000) -> tuple[str, dict]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read(max_chars + 1)
        return data[:max_chars], {"bytes": len(data)}
    except Exception:
        return "", {"bytes": 0}
