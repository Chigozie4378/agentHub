# --- Auth stub so Swagger has an 'Authorize' flow ---
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordRequestForm
from app.shared.db import Base, engine

# import models so they register with Base.metadata
from app.conversations import models as conversations_models  # noqa: F401
from app.runs import models as runs_models  # noqa: F401

# FILES
from app.files import models as files_models  # noqa: F401

# Routers Import
from app.files.api import router as files_router
from app.conversations.api import router as conversations_router
from app.tools.browser.api import router as browser_router
from app.tools.email.api import router as email_router
from app.runs.api import router as runs_router

TAGS_METADATA = [
    {"name": "Auth", "description": "Demo auth for Swagger 'Authorize' button"},
    {"name": "Conversations", "description": "Create, list, rename, archive chats"},
    {"name": "Health", "description": "Service health"},
]

app = FastAPI(
    title="AgentHub (Phase 0)",
    version="0.0.2",
    description="Chat-first, file-aware API (Phase 0).",
    openapi_tags=TAGS_METADATA,
)

# ---- DEV-ONLY error handler (helps you see real errors in Swagger) ----
import os
if os.getenv("ENV", "dev") == "dev":
    @app.exception_handler(Exception)
    async def _dev_ex_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"detail": str(exc)})

# ----------------------------------------------------------------------


@app.on_event("startup")
def _init_db():
    Base.metadata.create_all(bind=engine)

@app.get("/healthz", tags=["Health"])
def healthz():
    return {"ok": True}



@app.post("/auth/token", tags=["Auth"])
def auth_token(form: OAuth2PasswordRequestForm = Depends()):
    # Use any username/password in Swagger; we return a demo token.
    return {"access_token": "demo", "token_type": "bearer"}

# Mount feature routers
app.include_router(conversations_router)

# --- Custom OpenAPI: add bearerAuth + default security (you can fine-tune per route) ---
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})
    schema["components"]["securitySchemes"]["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    # Optional: make bearerAuth the default for all ops EXCEPT /auth/token and /healthz
    for path, ops in schema.get("paths", {}).items():
        if path in ["/auth/token", "/healthz"]:
            continue
        for op in ops.values():
            op.setdefault("security", [{"bearerAuth": []}])
    app.openapi_schema = schema
    return app.openapi_schema

from sqlalchemy import inspect

@app.get("/__debug/tables")
def _tables():
    return {"tables": inspect(engine).get_table_names()}

# Routers 
app.include_router(conversations_router)
app.include_router(files_router)
app.include_router(browser_router)
app.include_router(email_router)
app.include_router(runs_router)

app.openapi = custom_openapi
