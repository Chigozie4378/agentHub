# app/auth/api.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.shared.db import get_db
from app.shared.auth import create_access_token, get_user
from app.auth.service import register_user, authenticate_user
from app.shared.config import settings
from app.shared.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

class RegisterIn(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def api_register(inb: RegisterIn, db: Session = Depends(get_db)):
    try:
        user = register_user(db, inb.email, inb.password)
        return {"ok": True, "user": user}
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/token")
def api_token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    if settings.AUTH_DEMO:
        # return the demo token; user pastes it in Authorize
        return {"access_token": settings.DEMO_TOKEN, "token_type": "bearer", "demo": True}
    user = authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(401, "invalid credentials")
    token = create_access_token(sub=user["sub"], tier=user["tier"], role=user["role"])
    return {"access_token": token, "token_type": "bearer", "demo": False}

@router.get("/me")
def api_me(user = Depends(get_user)):
    return {"ok": True, "user": user}
