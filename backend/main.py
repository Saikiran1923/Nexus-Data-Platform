from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agents.capabilities import list_categories, total_capability_count
from backend.api.v1.router import api_router
from backend.config import get_settings
from backend.database.session import init_db
from backend.middleware.auth_middleware import JWTAuthMiddleware
from backend.schemas.common import ErrorResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Secure multi-tenant DataOps platform with JWT auth, RBAC, and audit logging.",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(JWTAuthMiddleware)
app.include_router(api_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        message = detail.get("message", str(detail))
        extra = detail
    else:
        message = str(detail)
        extra = None
    body = ErrorResponse(success=False, message=message, detail=extra)
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.get("/")
def root() -> dict:
    return {
        "project": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "api_prefix": "/api/v1",
        "capability_categories": len(list_categories()),
        "capability_count": total_capability_count(),
    }


@app.get("/health")
def health() -> dict:
    return {"status": "healthy", "environment": settings.environment}
