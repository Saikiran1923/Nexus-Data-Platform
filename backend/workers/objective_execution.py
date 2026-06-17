from __future__ import annotations

from datetime import datetime, timezone

from backend.database.session import SessionLocal
from backend.db_models.nexus_one import (
    BusinessObjective,
    ExecutionPhase,
    ExecutiveInsight,
    Project,
    TimelineEvent,
)
from backend.services.nexus_one_service import SubscriptionService
from backend.workers.celery_app import celery_app
from nexus_one.agent_runner import run_workforce_agent
from nexus_one.evidence_engine import EvidenceEngine
from nexus_one.impact_engine import calculate_business_impact, generate_executive_summary, generate_roi_analysis
from nexus_one.memory_graph import MemoryGraph
from nexus_one.workforce import get_agent_meta


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@celery_app.task(name="execute_objective", bind=True, max_retries=1)
def execute_objective(self, objective_id: str, tenant_id: str) -> dict:
    db = SessionLocal()
    try:
        objective = (
            db.query(BusinessObjective)
            .filter(BusinessObjective.id == objective_id, BusinessObjective.tenant_id == tenant_id)
            .first()
        )
        if not objective:
            return {"status": "not_found"}

        objective.status = "executing"
        objective.updated_at = _utcnow()
        db.commit()

        project = Project(
            tenant_id=tenant_id,
            objective_id=objective.id,
            name=f"Project: {objective.title}",
            status="executing",
        )
        db.add(project)
        db.flush()

        shared_memory: dict = {"agent_outputs": [], "objective_id": objective_id}
        memory_ctx = MemoryGraph.get_context_for_agents(db, tenant_id, objective_id)
        shared_memory.update(memory_ctx)

        context = {
            "task_id": objective.id,
            "title": objective.title,
            "description": objective.description,
            "category": objective.category,
        }

        agents = objective.selected_agents or []
        quality_scores: list[float] = []

        for phase_name, _ in [("planning", 1), ("validation", 2), ("execution", 3), ("qa", 4)]:
            phase = (
                db.query(ExecutionPhase)
                .filter(ExecutionPhase.objective_id == objective_id, ExecutionPhase.phase_name == phase_name)
                .first()
            )
            if phase:
                phase.status = "running"
                phase.started_at = _utcnow()
                db.commit()

        for agent_key in agents:
            meta = get_agent_meta(agent_key) or {"name": agent_key, "role": agent_key}
            db.add(TimelineEvent(
                objective_id=objective_id, phase="execution", event_type="agent_started",
                message=f"{meta['name']} started execution", status="running", agent_key=agent_key,
            ))
            db.commit()

            result = run_workforce_agent(agent_key, context, shared_memory)
            shared_memory["agent_outputs"].append(result.model_dump())
            quality_scores.append(95.0 if result.status == "SUCCESS" else 70.0)

            EvidenceEngine.record(
                db, tenant_id=tenant_id, objective_id=objective_id, project_id=project.id,
                agent_key=agent_key, agent_name=meta["name"],
                action=result.outputs.get("action", result.summary),
                input_summary=objective.description[:500],
                output_summary=result.summary,
                reason=f"Objective execution step for {objective.category}",
                impact=result.outputs.get("deliverable", "Deliverable produced"),
                evidence_metadata=result.outputs,
            )

            MemoryGraph.store(
                db, tenant_id=tenant_id, objective_id=objective_id,
                node_type="decision", title=f"{meta['name']} output",
                content={"agent": agent_key, "summary": result.summary, "outputs": result.outputs},
            )

            db.add(TimelineEvent(
                objective_id=objective_id, phase="execution", event_type="agent_completed",
                message=f"{meta['name']}: {result.summary}", status="success", agent_key=agent_key,
            ))
            db.commit()
            SubscriptionService.record_runtime(db, tenant_id, 0.5)

        for phase_name in ("planning", "validation", "execution", "qa"):
            phase = (
                db.query(ExecutionPhase)
                .filter(ExecutionPhase.objective_id == objective_id, ExecutionPhase.phase_name == phase_name)
                .first()
            )
            if phase:
                phase.status = "completed"
                phase.completed_at = _utcnow()

        approval_phase = (
            db.query(ExecutionPhase)
            .filter(ExecutionPhase.objective_id == objective_id, ExecutionPhase.phase_name == "approval")
            .first()
        )
        if approval_phase:
            approval_phase.status = "completed"
            approval_phase.completed_at = _utcnow()

        deploy_phase = (
            db.query(ExecutionPhase)
            .filter(ExecutionPhase.objective_id == objective_id, ExecutionPhase.phase_name == "deployment")
            .first()
        )
        if deploy_phase:
            deploy_phase.status = "completed"
            deploy_phase.completed_at = _utcnow()

        quality_score = round(sum(quality_scores) / max(len(quality_scores), 1), 1)
        impact = calculate_business_impact(
            complexity=objective.complexity or "medium",
            agent_count=len(agents),
            duration_hours=float(objective.estimated_duration_hours or 12),
            quality_score=quality_score,
            category=objective.category or "",
        )

        agent_names = [get_agent_meta(k).get("name", k) if get_agent_meta(k) else k for k in agents]
        evidence_count = len(shared_memory["agent_outputs"])
        exec_summary = generate_executive_summary(
            objective.title, objective.category or "", impact, agent_names, evidence_count,
        )

        objective.status = "completed"
        objective.current_phase = "deployment"
        objective.quality_score = quality_score
        objective.business_impact = impact
        objective.executive_summary = exec_summary
        objective.updated_at = _utcnow()

        project.status = "completed"
        project.quality_score = quality_score
        project.hours_saved = impact["hours_saved"]
        project.cost_savings = impact["cost_savings_usd"]
        project.revenue_impact = impact["revenue_impact_usd"]
        project.updated_at = _utcnow()

        roi = generate_roi_analysis(impact)
        db.add(ExecutiveInsight(
            tenant_id=tenant_id, objective_id=objective_id,
            summary=exec_summary,
            strategic_insights=[f"Category: {objective.category}", f"Complexity: {objective.complexity}"],
            recommendations=["Deploy to production", "Schedule quarterly review", "Share executive summary with stakeholders"],
            roi_analysis=roi,
            impact_report=impact,
        ))

        MemoryGraph.store(
            db, tenant_id=tenant_id, objective_id=objective_id,
            node_type="outcome", title="Execution completed",
            content={"impact": impact, "quality_score": quality_score},
        )

        db.add(TimelineEvent(
            objective_id=objective_id, phase="deployment", event_type="execution_complete",
            message="Objective execution completed successfully", status="success",
        ))
        db.commit()

        return {"status": "completed", "objective_id": objective_id, "quality_score": quality_score}
    except Exception as exc:
        db.rollback()
        objective = db.query(BusinessObjective).filter(BusinessObjective.id == objective_id).first()
        if objective:
            objective.status = "failed"
            objective.updated_at = _utcnow()
            db.commit()
        raise self.retry(exc=exc, countdown=10) from exc
    finally:
        db.close()
