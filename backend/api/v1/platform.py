from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from agents.capabilities import (
    build_capability_catalog,
    duties_for_category,
    list_categories,
    total_capability_count,
)
from agents.orchestrator.orchestrator import OrchestratorAgent
from backend.auth.dependencies import (
    ROLE_ADMIN,
    ROLE_APPROVER,
    ROLE_DEVELOPER,
    ROLE_REVIEWER,
    ROLE_USER,
    CurrentUser,
    require_roles,
)
from backend.schemas.common import APIResponse

router = APIRouter(tags=["platform"])


@router.get("/capabilities", response_model=APIResponse[dict])
def get_capabilities(
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_APPROVER, ROLE_USER)),
) -> APIResponse[dict]:
    return APIResponse(
        data={
            "total_categories": len(list_categories()),
            "total_capabilities": total_capability_count(),
            "categories": build_capability_catalog(),
        }
    )


@router.get("/capabilities/{category}", response_model=APIResponse[dict])
def get_capability_category(
    category: str,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_APPROVER, ROLE_USER)),
) -> APIResponse[dict]:
    matches = [c for c in list_categories() if c.lower() == category.lower()]
    if not matches:
        raise HTTPException(status_code=404, detail=f"Unknown capability category: {category}")
    resolved = matches[0]
    duties = duties_for_category(resolved)
    return APIResponse(
        data={
            "category": resolved,
            "duty_count": len(duties),
            "duties": duties,
        }
    )


@router.get("/agents", response_model=APIResponse[dict])
def get_agents(
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_APPROVER, ROLE_USER)),
) -> APIResponse[dict]:
    orchestrator = OrchestratorAgent()
    agents = orchestrator.list_agents()
    return APIResponse(data={"total_agents": len(agents), "agents": agents})
