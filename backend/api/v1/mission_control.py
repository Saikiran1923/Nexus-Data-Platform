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
from backend.schemas.nexus_one import EvidenceResponse, MissionControlDashboard
from backend.services.mission_control_service import MissionControlService
from nexus_one.evidence_engine import EvidenceEngine
from nexus_one.memory_graph import MemoryGraph

router = APIRouter(prefix="/mission-control", tags=["mission-control"])


@router.get("/dashboard", response_model=APIResponse[MissionControlDashboard])
def dashboard(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_APPROVER, ROLE_USER)),
) -> APIResponse[MissionControlDashboard]:
    data = MissionControlService.get_dashboard(db, current_user)
    return APIResponse(data=MissionControlDashboard(**data))


@router.get("/workforce", response_model=APIResponse[dict])
def workforce_board(
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_APPROVER, ROLE_USER)),
) -> APIResponse[dict]:
    return APIResponse(data=MissionControlService.get_workforce_board())


@router.get("/risks", response_model=APIResponse[list])
def risk_center(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_APPROVER)),
) -> APIResponse[list]:
    risks = MissionControlService.get_risk_center(db, current_user)
    return APIResponse(data=[
        {"id": r.id, "objective_id": r.objective_id, "risk_type": r.risk_type,
         "severity": r.severity, "description": r.description, "mitigation": r.mitigation}
        for r in risks
    ])


@router.get("/portfolio", response_model=APIResponse[list])
def portfolio(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_APPROVER, ROLE_USER)),
) -> APIResponse[list]:
    projects = MissionControlService.get_portfolio(db, current_user)
    return APIResponse(data=[
        {"id": p.id, "name": p.name, "status": p.status, "objective_id": p.objective_id,
         "quality_score": float(p.quality_score) if p.quality_score else None,
         "hours_saved": float(p.hours_saved), "cost_savings": float(p.cost_savings),
         "revenue_impact": float(p.revenue_impact)}
        for p in projects
    ])


@router.get("/executive-insights", response_model=APIResponse[list])
def executive_insights(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_APPROVER, ROLE_REVIEWER)),
) -> APIResponse[list]:
    insights = MissionControlService.get_executive_insights(db, current_user)
    return APIResponse(data=[
        {"id": i.id, "objective_id": i.objective_id, "summary": i.summary,
         "recommendations": i.recommendations, "roi_analysis": i.roi_analysis,
         "impact_report": i.impact_report, "created_at": i.created_at.isoformat()}
        for i in insights
    ])


@router.get("/evidence", response_model=APIResponse[list[EvidenceResponse]])
def evidence_center(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER, ROLE_APPROVER)),
) -> APIResponse[list[EvidenceResponse]]:
    records = EvidenceEngine.list_for_tenant(db, current_user.tenant_id)
    return APIResponse(data=[EvidenceResponse.model_validate(r) for r in records])


@router.get("/memory", response_model=APIResponse[list])
def memory_graph(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_REVIEWER)),
    node_type: str | None = None,
) -> APIResponse[list]:
    nodes = MemoryGraph.search(db, current_user.tenant_id, node_type=node_type)
    return APIResponse(data=[
        {"id": n.id, "node_type": n.node_type, "title": n.title, "content": n.content,
         "objective_id": n.objective_id, "created_at": n.created_at.isoformat()}
        for n in nodes
    ])
