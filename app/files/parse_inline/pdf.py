from pypdf import PdfReader

def extract_pdf_text(path: str, max_chars: int = 40_000) -> tuple[str, dict]:
    """
    Returns (text, meta). Meta: {"pages": N}
    """
    text_parts = []
    reader = PdfReader(path)
    for i, page in enumerate(reader.pages):
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if t:
            text_parts.append(f"\n\n--- Page {i+1} ---\n{t}")
        if sum(len(p) for p in text_parts) > max_chars:
            break
    full = "".join(text_parts)
    return full[:max_chars], {"pages": len(reader.pages)}
