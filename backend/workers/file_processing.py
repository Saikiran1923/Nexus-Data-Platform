from __future__ import annotations

from datetime import datetime, timezone

from backend.database.session import SessionLocal
from backend.db_models.data_upload import DataUpload
from backend.services.upload_service import UploadService
from backend.workers.celery_app import celery_app


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@celery_app.task(name="process_upload", bind=True, max_retries=2)
def process_upload(self, upload_id: str) -> dict:
    db = SessionLocal()
    try:
        upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
        if not upload:
            return {"upload_id": upload_id, "status": "not_found"}

        upload.processing_status = "processing"
        upload.updated_at = _utcnow()
        db.commit()

        file_path = UploadService.get_storage_path(upload)
        row_count, error = UploadService.process_file_content(file_path)

        upload.row_count = row_count
        upload.error_message = error
        upload.processing_status = "failed" if error else "completed"
        upload.updated_at = _utcnow()
        db.commit()

        return {
            "upload_id": upload_id,
            "processing_status": upload.processing_status,
            "row_count": row_count,
            "error_message": error,
        }
    except Exception as exc:
        db.rollback()
        upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
        if upload:
            upload.processing_status = "failed"
            upload.error_message = str(exc)
            upload.updated_at = _utcnow()
            db.commit()
        raise self.retry(exc=exc, countdown=5) from exc
    finally:
        db.close()
