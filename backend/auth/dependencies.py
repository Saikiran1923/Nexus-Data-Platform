from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, joinedload

from backend.auth.security import decode_access_token
from backend.database.session import get_db
from backend.db_models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

ROLE_ADMIN = "admin"
ROLE_DEVELOPER = "developer"
ROLE_REVIEWER = "reviewer"
ROLE_APPROVER = "approver"
ROLE_USER = "user"


@dataclass
class CurrentUser:
    id: str
    tenant_id: str
    email: str
    role: str
    full_name: str | None


def _load_user(db: Session, user_id: str) -> User:
    user = (
        db.query(User)
        .options(joinedload(User.role))
        .filter(User.id == user_id, User.is_active.is_(True))
        .first()
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Missing subject")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = _load_user(db, user_id)
    if payload.get("tenant_id") and payload["tenant_id"] != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tenant mismatch")

    request.state.user_id = user.id
    request.state.tenant_id = user.tenant_id
    return CurrentUser(
        id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        role=user.role.name,
        full_name=user.full_name,
    )


def require_roles(*allowed_roles: str) -> Callable:
    allowed = set(allowed_roles)

    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not permitted for this action",
            )
        return current_user

    return dependency


def require_any_role(roles: Iterable[str]) -> Callable:
    return require_roles(*roles)
