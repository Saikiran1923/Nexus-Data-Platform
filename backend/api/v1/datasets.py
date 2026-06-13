from __future__ import annotations

from fastapi import APIRouter, Depends, Request
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
from backend.schemas.api import DatasetCreateRequest, DatasetResponse
from backend.schemas.common import APIResponse
from backend.services.dataset_service import DatasetService

router = APIRouter(prefix="/datasets", tags=["datasets"])


def _client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


@router.post("", response_model=APIResponse[DatasetResponse])
def create_dataset(
    payload: DatasetCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER)),
) -> APIResponse[DatasetResponse]:
    dataset = DatasetService.create(
        db,
        current_user,
        name=payload.name,
        description=payload.description,
        ip_address=_client_ip(request),
    )
    return APIResponse(message="Dataset created", data=DatasetResponse.model_validate(dataset))


@router.get("", response_model=APIResponse[list[DatasetResponse]])
def list_datasets(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_USER)),
) -> APIResponse[list[DatasetResponse]]:
    datasets = DatasetService.list_for_tenant(db, current_user)
    return APIResponse(data=[DatasetResponse.model_validate(d) for d in datasets])


@router.get("/{dataset_id}", response_model=APIResponse[DatasetResponse])
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_USER)),
) -> APIResponse[DatasetResponse]:
    dataset = DatasetService.get(db, current_user, dataset_id)
    return APIResponse(data=DatasetResponse.model_validate(dataset))


@router.delete("/{dataset_id}", response_model=APIResponse[None])
def delete_dataset(
    dataset_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER)),
) -> APIResponse[None]:
    DatasetService.delete(db, current_user, dataset_id, ip_address=_client_ip(request))
    return APIResponse(message="Dataset deleted")
