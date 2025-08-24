from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from app.shared.guard import guard_gate, bump_after_tool

router = APIRouter(prefix="/tools/sentiment", tags=["Tools: Sentiment"])

class SentReq(BaseModel):
    text: str

_an = SentimentIntensityAnalyzer()

@router.post("", summary="Analyze sentiment (VADER)")
def analyze_sentiment(req: SentReq, ctx=Depends(guard_gate("sentiment"))):
    s = _an.polarity_scores(req.text)
    # map to label
    label = "neutral"
    if s["compound"] >= 0.05: label = "positive"
    elif s["compound"] <= -0.05: label = "negative"
    bump_after_tool(ctx, token_cost=900)
    return {"ok": True, "label": label, "scores": s}
