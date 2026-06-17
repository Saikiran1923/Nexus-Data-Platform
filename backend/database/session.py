from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config import get_settings
from backend.db_models.base import Base

settings = get_settings()

connect_args: dict = {}
engine_kwargs: dict = {"pool_pre_ping": True}

if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    if ":memory:" in settings.database_url:
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    from backend.db_models import audit_log, data_upload, dataset, role, task, tenant, user  # noqa: F401
    from backend.db_models import nexus_one  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _seed_roles()
    _seed_nexus_one()


def _seed_nexus_one() -> None:
    from backend.services.nexus_one_service import CouponService, SubscriptionService

    db = SessionLocal()
    try:
        SubscriptionService.seed_plans(db)
        CouponService.seed_coupons(db)
    finally:
        db.close()


def _seed_roles() -> None:
    from backend.db_models.role import Role

    defaults = [
        ("admin", "Full platform access including pipeline approval"),
        ("developer", "Create tasks, upload data, run pipelines"),
        ("reviewer", "Read-only access to tenant data and audit logs"),
        ("approver", "Approve deployments after admin pipeline approval"),
        ("user", "Basic authenticated access within tenant"),
    ]
    db = SessionLocal()
    try:
        existing = {r.name for r in db.query(Role).all()}
        for name, description in defaults:
            if name not in existing:
                db.add(Role(name=name, description=description))
        db.commit()
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
