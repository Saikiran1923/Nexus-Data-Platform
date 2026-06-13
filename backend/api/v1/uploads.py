from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from backend.auth.dependencies import (
    ROLE_ADMIN,
    ROLE_DEVELOPER,
    ROLE_REVIEWER,
    ROLE_USER,
    CurrentUser,
    require_roles,
)
from backend.database.session import get_db
from backend.schemas.api import UploadResponse, UploadStatusResponse
from backend.schemas.common import APIResponse
from backend.services.upload_service import UploadService
from backend.workers.file_processing import process_upload

router = APIRouter(prefix="/uploads", tags=["uploads"])


def _client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


@router.post("", response_model=APIResponse[list[UploadResponse]])
async def upload_files(
    request: Request,
    files: list[UploadFile] = File(...),
    dataset_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER)),
) -> APIResponse[list[UploadResponse]]:
    if not files:
        return APIResponse(success=False, message="No files provided", data=[])

    saved = UploadService.save_uploads(
        db,
        current_user,
        files,
        dataset_id=dataset_id,
        ip_address=_client_ip(request),
    )
    for upload in saved:
        process_upload.delay(upload.id)

    return APIResponse(
        message="Files uploaded; processing started",
        data=[UploadResponse.model_validate(u) for u in saved],
    )


@router.get("", response_model=APIResponse[list[UploadResponse]])
def list_uploads(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_USER)),
) -> APIResponse[list[UploadResponse]]:
    uploads = UploadService.list_for_tenant(db, current_user)
    return APIResponse(data=[UploadResponse.model_validate(u) for u in uploads])


@router.get("/{upload_id}", response_model=APIResponse[UploadResponse])
def get_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_USER)),
) -> APIResponse[UploadResponse]:
    upload = UploadService.get(db, current_user, upload_id)
    return APIResponse(data=UploadResponse.model_validate(upload))


@router.get("/{upload_id}/status", response_model=APIResponse[UploadStatusResponse])
def get_upload_status(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_USER)),
) -> APIResponse[UploadStatusResponse]:
    upload = UploadService.get(db, current_user, upload_id)
    return APIResponse(
        data=UploadStatusResponse(
            id=upload.id,
            upload_status=upload.upload_status,
            processing_status=upload.processing_status,
            row_count=upload.row_count,
            error_message=upload.error_message,
            updated_at=upload.updated_at,
        )
    )


@router.delete("/{upload_id}", response_model=APIResponse[None])
def delete_upload(
    upload_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER)),
) -> APIResponse[None]:
    UploadService.delete(db, current_user, upload_id, ip_address=_client_ip(request))
    return APIResponse(message="Upload deleted")
