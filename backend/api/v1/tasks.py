from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.auth.dependencies import (
    ROLE_ADMIN,
    ROLE_APPROVER,
    ROLE_DEVELOPER,
    ROLE_REVIEWER,
    ROLE_USER,
    CurrentUser,
    require_roles,
)
from backend.database.session import get_db
from backend.schemas.api import ApprovalRequest, TaskCreateRequest, TaskResponse
from backend.schemas.common import APIResponse
from backend.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


@router.post("", response_model=APIResponse[TaskResponse])
def create_task(
    payload: TaskCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER)),
) -> APIResponse[TaskResponse]:
    task = TaskService.create(db, current_user, payload, ip_address=_client_ip(request))
    return APIResponse(message="Task created", data=task)


@router.get("", response_model=APIResponse[list[TaskResponse]])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_APPROVER, ROLE_USER)),
) -> APIResponse[list[TaskResponse]]:
    tasks = TaskService.list_for_tenant(db, current_user)
    return APIResponse(data=tasks)


@router.get("/{task_id}", response_model=APIResponse[TaskResponse])
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_APPROVER, ROLE_USER)),
) -> APIResponse[TaskResponse]:
    task = TaskService.get(db, current_user, task_id)
    return APIResponse(data=task)


@router.post("/{task_id}/run", response_model=APIResponse[TaskResponse])
def run_task(
    task_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER)),
) -> APIResponse[TaskResponse]:
    task = TaskService.run(db, current_user, task_id, ip_address=_client_ip(request))
    return APIResponse(message="Task executed", data=task)


@router.post("/{task_id}/approval", response_model=APIResponse[TaskResponse])
def approve_task(
    task_id: str,
    approval: ApprovalRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN)),
) -> APIResponse[TaskResponse]:
    task = TaskService.approve(db, current_user, task_id, approval, ip_address=_client_ip(request))
    return APIResponse(message="Approval recorded", data=task)


@router.post("/{task_id}/deploy", response_model=APIResponse[TaskResponse])
def deploy_task(
    task_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_APPROVER)),
) -> APIResponse[TaskResponse]:
    task = TaskService.deploy(db, current_user, task_id, ip_address=_client_ip(request))
    return APIResponse(message="Task deployed", data=task)
