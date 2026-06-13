from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.auth.dependencies import CurrentUser, get_current_user
from backend.config import get_settings
from backend.database.session import get_db
from backend.schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserResponse
from backend.schemas.common import APIResponse
from backend.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.post("/signup", response_model=APIResponse[TokenResponse])
def signup(payload: SignupRequest, request: Request, db: Session = Depends(get_db)) -> APIResponse[TokenResponse]:
    user, token = AuthService.signup(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        tenant_name=payload.tenant_name,
        tenant_slug=payload.tenant_slug,
        ip_address=_client_ip(request),
    )
    return APIResponse(
        message="Account created",
        data=TokenResponse(
            access_token=token,
            expires_in_minutes=settings.jwt_access_token_expire_minutes,
        ),
    )


@router.post("/login", response_model=APIResponse[TokenResponse])
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> APIResponse[TokenResponse]:
    user, token = AuthService.login(
        db,
        email=payload.email,
        password=payload.password,
        tenant_slug=payload.tenant_slug,
        ip_address=_client_ip(request),
    )
    return APIResponse(
        message="Login successful",
        data=TokenResponse(
            access_token=token,
            expires_in_minutes=settings.jwt_access_token_expire_minutes,
        ),
    )


@router.get("/me", response_model=APIResponse[UserResponse])
def me(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponse[UserResponse]:
    user = AuthService.get_profile(db, current_user)
    return APIResponse(
        data=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.name,
            tenant_id=user.tenant_id,
        )
    )
