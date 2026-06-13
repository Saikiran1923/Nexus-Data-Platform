from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from backend.db_models.base import Base, new_uuid, utcnow

if TYPE_CHECKING:
    from backend.db_models.tenant import Tenant
    from backend.db_models.user import User

_json_type = JSON().with_variant(JSONB(), "postgresql")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="CREATED", nullable=False, index=True)
    selected_agents: Mapped[list[str] | None] = mapped_column(_json_type, nullable=True)
    results: Mapped[list[dict[str, Any]] | None] = mapped_column(_json_type, nullable=True)
    qa_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    human_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deployment_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="tasks")
    creator: Mapped["User"] = relationship("User", back_populates="tasks")
