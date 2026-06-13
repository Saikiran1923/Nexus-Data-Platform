from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db_models.base import Base, new_uuid, utcnow

if TYPE_CHECKING:
    from backend.db_models.data_upload import DataUpload
    from backend.db_models.tenant import Tenant
    from backend.db_models.user import User


class Dataset(Base):
    __tablename__ = "datasets"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_datasets_tenant_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="datasets")
    creator: Mapped["User"] = relationship("User", back_populates="datasets")
    uploads: Mapped[List["DataUpload"]] = relationship("DataUpload", back_populates="dataset")
