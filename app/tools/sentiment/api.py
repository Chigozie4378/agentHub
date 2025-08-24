from fastapi import APIRouter
from pydantic import BaseModel
from .service import analyze_sentiment

router = APIRouter(prefix="/tools/sentiment", tags=["Tools: Sentiment"])

class SentimentIn(BaseModel):
    text: str

@router.post("/analyze")
def api_sentiment(inb: SentimentIn):
    return analyze_sentiment(text=inb.text)
