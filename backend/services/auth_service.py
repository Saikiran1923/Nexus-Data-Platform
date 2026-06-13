from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.auth.dependencies import CurrentUser
from backend.auth.security import create_access_token, hash_password, verify_password
from backend.config import get_settings
from backend.db_models.role import Role
from backend.db_models.tenant import Tenant
from backend.db_models.user import User
from backend.services.audit_service import AuditService

settings = get_settings()


class AuthService:
    @staticmethod
    def signup(
        db: Session,
        *,
        email: str,
        password: str,
        full_name: str | None,
        tenant_name: str,
        tenant_slug: str,
        ip_address: str | None = None,
    ) -> tuple[User, str]:
        if db.query(Tenant).filter(Tenant.slug == tenant_slug).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant slug already exists")

        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Roles not seeded")

        tenant = Tenant(name=tenant_name, slug=tenant_slug)
        db.add(tenant)
        db.flush()

        user = User(
            tenant_id=tenant.id,
            role_id=admin_role.id,
            email=email.lower(),
            password_hash=hash_password(password),
            full_name=full_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        AuditService.log(
            db,
            action="signup",
            user_id=user.id,
            tenant_id=tenant.id,
            resource_type="user",
            resource_id=user.id,
            details={"email": email, "tenant_slug": tenant_slug},
            ip_address=ip_address,
        )
        token = AuthService._build_token(user)
        return user, token

    @staticmethod
    def login(
        db: Session,
        *,
        email: str,
        password: str,
        tenant_slug: str,
        ip_address: str | None = None,
    ) -> tuple[User, str]:
        tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug, Tenant.is_active.is_(True)).first()
        if not tenant:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        user = (
            db.query(User)
            .options(joinedload(User.role))
            .filter(User.tenant_id == tenant.id, User.email == email.lower(), User.is_active.is_(True))
            .first()
        )
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        AuditService.log(
            db,
            action="login",
            user_id=user.id,
            tenant_id=tenant.id,
            resource_type="user",
            resource_id=user.id,
            ip_address=ip_address,
        )
        return user, AuthService._build_token(user)

    @staticmethod
    def _build_token(user: User) -> str:
        return create_access_token(
            user.id,
            claims={"tenant_id": user.tenant_id, "role": user.role.name, "email": user.email},
        )

    @staticmethod
    def get_profile(db: Session, current_user: CurrentUser) -> User:
        user = (
            db.query(User)
            .options(joinedload(User.role))
            .filter(User.id == current_user.id, User.tenant_id == current_user.tenant_id)
            .first()
        )
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
