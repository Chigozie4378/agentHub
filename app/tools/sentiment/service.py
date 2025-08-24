
def analyze_sentiment(text: str):
    t = (text or "").lower()
    pos = sum(w in t for w in ["good","great","awesome","love","excellent","nice","happy"])
    neg = sum(w in t for w in ["bad","terrible","hate","awful","sad","angry"])
    label = "neutral"
    if pos > neg: label = "positive"
    elif neg > pos: label = "negative"
    return {"ok": True, "label": label, "scores": {"positive": pos, "negative": neg}}
