from __future__ import annotations

import csv
import os
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import CurrentUser
from backend.config import get_settings
from backend.db_models.data_upload import DataUpload
from backend.db_models.dataset import Dataset
from backend.services.audit_service import AuditService

settings = get_settings()


class UploadService:
    @staticmethod
    def _tenant_upload_dir(tenant_id: str) -> Path:
        path = Path(settings.upload_dir) / tenant_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _validate_file(file: UploadFile, content: bytes) -> None:
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

        if len(content) > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {settings.max_upload_size_bytes} bytes",
            )

        filename = file.filename or ""
        ext = Path(filename).suffix.lower()
        if ext not in settings.allowed_upload_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {settings.allowed_upload_extensions}",
            )

        content_type = (file.content_type or "").lower()
        if content_type and content_type not in settings.allowed_upload_content_types:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content type")

        try:
            sample = content[:8192].decode("utf-8-sig")
            csv.Sniffer().sniff(sample, delimiters=",;\t")
        except (UnicodeDecodeError, csv.Error) as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CSV content") from exc

    @staticmethod
    def _safe_filename(name: str) -> str:
        base = Path(name).name
        return re.sub(r"[^A-Za-z0-9._-]", "_", base)[:200]

    @staticmethod
    def save_uploads(
        db: Session,
        current_user: CurrentUser,
        files: list[UploadFile],
        dataset_id: str | None = None,
        ip_address: str | None = None,
    ) -> list[DataUpload]:
        if dataset_id:
            dataset = (
                db.query(Dataset)
                .filter(Dataset.id == dataset_id, Dataset.tenant_id == current_user.tenant_id)
                .first()
            )
            if not dataset:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

        saved: list[DataUpload] = []
        tenant_dir = UploadService._tenant_upload_dir(current_user.tenant_id)

        for file in files:
            content = file.file.read()
            UploadService._validate_file(file, content)

            stored_name = f"{uuid.uuid4().hex}.csv"
            stored_path = tenant_dir / stored_name
            stored_path.write_bytes(content)

            upload = DataUpload(
                tenant_id=current_user.tenant_id,
                user_id=current_user.id,
                dataset_id=dataset_id,
                original_filename=UploadService._safe_filename(file.filename or "upload.csv"),
                stored_filename=stored_name,
                content_type=file.content_type,
                file_size_bytes=len(content),
                upload_status="completed",
                processing_status="pending",
            )
            db.add(upload)
            db.flush()

            AuditService.log(
                db,
                action="file_upload",
                user_id=current_user.id,
                tenant_id=current_user.tenant_id,
                resource_type="data_upload",
                resource_id=upload.id,
                details={"filename": upload.original_filename, "size": len(content)},
                ip_address=ip_address,
            )
            saved.append(upload)

        db.commit()
        for upload in saved:
            db.refresh(upload)
        return saved

    @staticmethod
    def list_for_tenant(db: Session, current_user: CurrentUser) -> list[DataUpload]:
        return (
            db.query(DataUpload)
            .filter(DataUpload.tenant_id == current_user.tenant_id)
            .order_by(DataUpload.created_at.desc())
            .all()
        )

    @staticmethod
    def get(db: Session, current_user: CurrentUser, upload_id: str) -> DataUpload:
        upload = (
            db.query(DataUpload)
            .filter(DataUpload.id == upload_id, DataUpload.tenant_id == current_user.tenant_id)
            .first()
        )
        if not upload:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")

        AuditService.log(
            db,
            action="data_access",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            resource_type="data_upload",
            resource_id=upload.id,
        )
        return upload

    @staticmethod
    def get_storage_path(upload: DataUpload) -> Path:
        return Path(settings.upload_dir) / upload.tenant_id / upload.stored_filename

    @staticmethod
    def delete(db: Session, current_user: CurrentUser, upload_id: str, ip_address: str | None = None) -> None:
        upload = UploadService.get(db, current_user, upload_id)
        storage_path = UploadService.get_storage_path(upload)
        if storage_path.exists():
            storage_path.unlink()

        db.delete(upload)
        db.commit()
        AuditService.log(
            db,
            action="data_deletion",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            resource_type="data_upload",
            resource_id=upload_id,
            ip_address=ip_address,
        )

    @staticmethod
    def process_file_content(file_path: Path) -> tuple[int, str | None]:
        try:
            with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.reader(handle)
                rows = list(reader)
            if not rows:
                return 0, "CSV file has no rows"
            header = rows[0]
            if not any(cell.strip() for cell in header):
                return 0, "CSV header row is empty"
            data_rows = [row for row in rows[1:] if any(cell.strip() for cell in row)]
            return len(data_rows), None
        except OSError as exc:
            return 0, f"Failed to read file: {exc}"
        except csv.Error as exc:
            return 0, f"CSV parse error: {exc}"
