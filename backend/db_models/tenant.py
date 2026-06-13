from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db_models.base import Base, new_uuid, utcnow

if TYPE_CHECKING:
    from backend.db_models.data_upload import DataUpload
    from backend.db_models.dataset import Dataset
    from backend.db_models.task import Task
    from backend.db_models.user import User


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    users: Mapped[List["User"]] = relationship("User", back_populates="tenant")
    datasets: Mapped[List["Dataset"]] = relationship("Dataset", back_populates="tenant")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="tenant")
    uploads: Mapped[List["DataUpload"]] = relationship("DataUpload", back_populates="tenant")
