# app/tools/sentiment/api.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.shared.http import ok, err
from app.shared.guard import guard_gate, bump_after_tool
from .service import analyze_sentiment

router = APIRouter(prefix="/tools/sentiment", tags=["Tools: Sentiment"])

class SentimentIn(BaseModel):
    text: str

@router.post("/analyze")
def api_sentiment(inb: SentimentIn, ctx=Depends(guard_gate("sentiment"))):
    try:
        out = analyze_sentiment(inb.text)
        bump_after_tool(ctx, token_cost=1200)
        return ok(out)
    except ValueError as e:
        return err("invalid_input", status=400, details=str(e))
    except Exception as e:
        return err("tool_failed", status=500, details=str(e))
