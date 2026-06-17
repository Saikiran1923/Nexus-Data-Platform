from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.db_models.nexus_one import EvidenceRecord


class EvidenceEngine:
    @staticmethod
    def record(
        db: Session,
        *,
        tenant_id: str,
        objective_id: str,
        project_id: str | None,
        agent_key: str,
        agent_name: str,
        action: str,
        input_summary: str | None = None,
        output_summary: str | None = None,
        reason: str | None = None,
        impact: str | None = None,
        evidence_metadata: dict[str, Any] | None = None,
    ) -> EvidenceRecord:
        evidence = EvidenceRecord(
            tenant_id=tenant_id,
            objective_id=objective_id,
            project_id=project_id,
            agent_key=agent_key,
            agent_name=agent_name,
            action=action,
            input_summary=input_summary,
            output_summary=output_summary,
            reason=reason,
            impact=impact,
            evidence_metadata=evidence_metadata,
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        return evidence

    @staticmethod
    def list_for_objective(db: Session, tenant_id: str, objective_id: str) -> list[EvidenceRecord]:
        return (
            db.query(EvidenceRecord)
            .filter(EvidenceRecord.tenant_id == tenant_id, EvidenceRecord.objective_id == objective_id)
            .order_by(EvidenceRecord.created_at.asc())
            .all()
        )

    @staticmethod
    def list_for_tenant(db: Session, tenant_id: str, limit: int = 100) -> list[EvidenceRecord]:
        return (
            db.query(EvidenceRecord)
            .filter(EvidenceRecord.tenant_id == tenant_id)
            .order_by(EvidenceRecord.created_at.desc())
            .limit(limit)
            .all()
        )
