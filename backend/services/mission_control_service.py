from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.auth.dependencies import CurrentUser
from backend.db_models.nexus_one import (
    BusinessObjective,
    EvidenceRecord,
    ExecutiveInsight,
    ObjectiveRisk,
    Project,
    TimelineEvent,
)
from nexus_one.workforce import list_all_agents


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MissionControlService:
    @staticmethod
    def get_dashboard(db: Session, current_user: CurrentUser) -> dict[str, Any]:
        tenant_id = current_user.tenant_id

        objectives = db.query(BusinessObjective).filter(BusinessObjective.tenant_id == tenant_id).all()
        running = [o for o in objectives if o.status in ("executing", "analyzed", "running")]
        completed = [o for o in objectives if o.status in ("completed", "deployed")]

        projects = db.query(Project).filter(Project.tenant_id == tenant_id).all()
        avg_quality = (
            db.query(func.avg(BusinessObjective.quality_score))
            .filter(BusinessObjective.tenant_id == tenant_id, BusinessObjective.quality_score.isnot(None))
            .scalar()
        ) or 0.0

        total_hours_saved = sum(float(p.hours_saved or 0) for p in projects)
        total_cost_savings = sum(float(p.cost_savings or 0) for p in projects)
        total_revenue = sum(float(p.revenue_impact or 0) for p in projects)

        active_agents = len(list_all_agents())
        open_risks = (
            db.query(ObjectiveRisk)
            .filter(ObjectiveRisk.tenant_id == tenant_id, ObjectiveRisk.is_resolved.is_(False))
            .count()
        )

        from backend.services.nexus_one_service import SubscriptionService
        subscription = SubscriptionService.get_plan_limits(db, tenant_id)

        return {
            "kpis": {
                "business_objectives": len(objectives),
                "running_projects": len(running),
                "completed_projects": len(completed),
                "active_agents": active_agents,
                "quality_score": round(float(avg_quality), 1),
                "hours_saved": round(total_hours_saved, 1),
                "cost_savings_usd": round(total_cost_savings, 2),
                "revenue_impact_usd": round(total_revenue, 2),
            },
            "subscription": subscription,
            "open_risks": open_risks,
            "recent_objectives": [
                {"id": o.id, "title": o.title, "status": o.status, "category": o.category, "phase": o.current_phase}
                for o in sorted(objectives, key=lambda x: x.created_at, reverse=True)[:8]
            ],
        }

    @staticmethod
    def get_workforce_board() -> dict[str, Any]:
        from nexus_one.workforce import WORKFORCE_DEPARTMENTS

        board: dict[str, Any] = {}
        for dept, agents in WORKFORCE_DEPARTMENTS.items():
            board[dept] = {
                "department": dept.replace("_", " ").title(),
                "agent_count": len(agents),
                "agents": [{**a, "status": "available"} for a in agents],
            }
        return {"departments": board, "total_agents": len(list_all_agents())}

    @staticmethod
    def get_timeline(db: Session, current_user: CurrentUser, objective_id: str) -> list[TimelineEvent]:
        return (
            db.query(TimelineEvent)
            .join(BusinessObjective, TimelineEvent.objective_id == BusinessObjective.id)
            .filter(BusinessObjective.tenant_id == current_user.tenant_id, TimelineEvent.objective_id == objective_id)
            .order_by(TimelineEvent.created_at.asc())
            .all()
        )

    @staticmethod
    def get_risk_center(db: Session, current_user: CurrentUser) -> list[ObjectiveRisk]:
        return (
            db.query(ObjectiveRisk)
            .filter(ObjectiveRisk.tenant_id == current_user.tenant_id, ObjectiveRisk.is_resolved.is_(False))
            .order_by(ObjectiveRisk.created_at.desc())
            .limit(50)
            .all()
        )

    @staticmethod
    def get_portfolio(db: Session, current_user: CurrentUser) -> list[Project]:
        return (
            db.query(Project)
            .filter(Project.tenant_id == current_user.tenant_id)
            .order_by(Project.created_at.desc())
            .all()
        )

    @staticmethod
    def get_executive_insights(db: Session, current_user: CurrentUser, limit: int = 10) -> list[ExecutiveInsight]:
        return (
            db.query(ExecutiveInsight)
            .filter(ExecutiveInsight.tenant_id == current_user.tenant_id)
            .order_by(ExecutiveInsight.created_at.desc())
            .limit(limit)
            .all()
        )
