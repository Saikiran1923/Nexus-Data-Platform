from __future__ import annotations

from fastapi import APIRouter, Depends
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
from backend.schemas.common import APIResponse
from backend.schemas.nexus_one import ObjectiveCreateRequest, ObjectiveResponse, TimelineEventResponse
from backend.services.mission_control_service import MissionControlService
from backend.services.nexus_one_service import ObjectiveService
from backend.workers.objective_execution import execute_objective

router = APIRouter(prefix="/objectives", tags=["objectives"])


@router.post("", response_model=APIResponse[ObjectiveResponse])
def create_objective(
    payload: ObjectiveCreateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_USER)),
) -> APIResponse[ObjectiveResponse]:
    objective = ObjectiveService.create(db, current_user, title=payload.title, description=payload.description)
    return APIResponse(message="Objective analyzed and execution plan created", data=ObjectiveResponse.model_validate(objective))


@router.get("", response_model=APIResponse[list[ObjectiveResponse]])
def list_objectives(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_APPROVER, ROLE_USER)),
) -> APIResponse[list[ObjectiveResponse]]:
    objectives = ObjectiveService.list_for_tenant(db, current_user)
    return APIResponse(data=[ObjectiveResponse.model_validate(o) for o in objectives])


@router.get("/{objective_id}", response_model=APIResponse[ObjectiveResponse])
def get_objective(
    objective_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_APPROVER, ROLE_USER)),
) -> APIResponse[ObjectiveResponse]:
    objective = ObjectiveService.get(db, current_user, objective_id)
    return APIResponse(data=ObjectiveResponse.model_validate(objective))


@router.post("/{objective_id}/execute", response_model=APIResponse[dict])
def execute_objective_endpoint(
    objective_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER)),
) -> APIResponse[dict]:
    objective = ObjectiveService.get(db, current_user, objective_id)
    execute_objective.delay(objective.id, current_user.tenant_id)
    return APIResponse(message="Execution started", data={"objective_id": objective.id, "status": "executing"})


@router.get("/{objective_id}/timeline", response_model=APIResponse[list[TimelineEventResponse]])
def get_timeline(
    objective_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_APPROVER, ROLE_USER)),
) -> APIResponse[list[TimelineEventResponse]]:
    ObjectiveService.get(db, current_user, objective_id)
    events = MissionControlService.get_timeline(db, current_user, objective_id)
    return APIResponse(data=[TimelineEventResponse.model_validate(e) for e in events])
