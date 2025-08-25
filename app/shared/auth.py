# app/shared/auth.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError  # python-jose[cryptography]

from app.shared.config import settings

bearer = HTTPBearer(auto_error=False, scheme_name="bearerAuth")

def create_access_token(
    sub: str,
    tier: str = "free",
    role: str = "user",
    extra: Optional[Dict[str, Any]] = None,
    minutes: Optional[int] = None,
) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=minutes or settings.JWT_EXPIRE_MIN)
    payload: Dict[str, Any] = {
        "sub": sub,
        "tier": tier,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if settings.JWT_ISS:
        payload["iss"] = settings.JWT_ISS
    if settings.JWT_AUD:
        payload["aud"] = settings.JWT_AUD
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_KEY, algorithm=settings.JWT_ALG)

def issue_dev_token(sub: str, tier: str = "dev", role: str = "user") -> str:
    """Helper used by main.py to issue a short-lived dev JWT."""
    return create_access_token(sub=sub, tier=tier, role=role)

def get_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    # Always require a bearer token
    if not creds:
        raise HTTPException(401, "missing bearer token")

    token = creds.credentials

    # Demo shortcut (strict: must match DEMO_TOKEN exactly)
    if settings.AUTH_DEMO and token == settings.DEMO_TOKEN:
        return {"sub": "demo-user", "tier": "free", "role": "user", "mode": "demo"}

    # Otherwise, validate real JWT
    try:
        payload = jwt.decode(
            token,
            settings.JWT_KEY,
            algorithms=[settings.JWT_ALG],
            audience=settings.JWT_AUD,
            issuer=settings.JWT_ISS,
            options={
                "verify_aud": bool(settings.JWT_AUD),
                "verify_iss": bool(settings.JWT_ISS),
            },
        )
    except JWTError as e:
        raise HTTPException(401, f"invalid token: {e}")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(401, "invalid token: missing sub")

    return {
        "sub": sub,
        "tier": payload.get("tier", "free"),
        "role": payload.get("role", "user"),
        "mode": "jwt",
    }
