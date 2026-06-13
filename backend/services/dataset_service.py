from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import CurrentUser
from backend.db_models.dataset import Dataset
from backend.services.audit_service import AuditService


class DatasetService:
    @staticmethod
    def create(
        db: Session,
        current_user: CurrentUser,
        *,
        name: str,
        description: str | None,
        ip_address: str | None = None,
    ) -> Dataset:
        existing = (
            db.query(Dataset)
            .filter(Dataset.tenant_id == current_user.tenant_id, Dataset.name == name)
            .first()
        )
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dataset name already exists")

        dataset = Dataset(
            tenant_id=current_user.tenant_id,
            created_by=current_user.id,
            name=name,
            description=description,
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        AuditService.log(
            db,
            action="dataset_create",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            resource_type="dataset",
            resource_id=dataset.id,
            details={"name": name},
            ip_address=ip_address,
        )
        return dataset

    @staticmethod
    def list_for_tenant(db: Session, current_user: CurrentUser) -> list[Dataset]:
        return (
            db.query(Dataset)
            .filter(Dataset.tenant_id == current_user.tenant_id)
            .order_by(Dataset.created_at.desc())
            .all()
        )

    @staticmethod
    def get(db: Session, current_user: CurrentUser, dataset_id: str) -> Dataset:
        dataset = (
            db.query(Dataset)
            .filter(Dataset.id == dataset_id, Dataset.tenant_id == current_user.tenant_id)
            .first()
        )
        if not dataset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

        AuditService.log(
            db,
            action="data_access",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            resource_type="dataset",
            resource_id=dataset.id,
        )
        return dataset

    @staticmethod
    def delete(db: Session, current_user: CurrentUser, dataset_id: str, ip_address: str | None = None) -> None:
        dataset = DatasetService.get(db, current_user, dataset_id)
        db.delete(dataset)
        db.commit()
        AuditService.log(
            db,
            action="data_deletion",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            resource_type="dataset",
            resource_id=dataset_id,
            ip_address=ip_address,
        )
