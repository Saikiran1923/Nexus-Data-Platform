from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db_models.base import Base, new_uuid, utcnow

if TYPE_CHECKING:
    from backend.db_models.audit_log import AuditLog
    from backend.db_models.data_upload import DataUpload
    from backend.db_models.dataset import Dataset
    from backend.db_models.role import Role
    from backend.db_models.task import Task
    from backend.db_models.tenant import Tenant


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    role: Mapped["Role"] = relationship("Role", back_populates="users")
    datasets: Mapped[List["Dataset"]] = relationship("Dataset", back_populates="creator")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="creator")
    uploads: Mapped[List["DataUpload"]] = relationship("DataUpload", back_populates="user")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user")
