from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.auth.security import decode_access_token


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Reject unauthenticated requests to /api/v1 protected routes."""

    PUBLIC_EXACT = {"/", "/health", "/docs", "/redoc", "/openapi.json"}
    PUBLIC_API = {"/api/v1/auth/signup", "/api/v1/auth/login"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in self.PUBLIC_EXACT or path in self.PUBLIC_API:
            return await call_next(request)

        if not path.startswith("/api/v1"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Not authenticated", "detail": "Missing Bearer token"},
            )

        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = decode_access_token(token)
            request.state.token_payload = payload
            request.state.user_id = payload.get("sub")
            request.state.tenant_id = payload.get("tenant_id")
        except ValueError as exc:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": str(exc), "detail": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)
