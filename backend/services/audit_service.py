from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.db_models.audit_log import AuditLog


class AuditService:
    @staticmethod
    def log(
        db: Session,
        *,
        action: str,
        user_id: str | None = None,
        tenant_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            action=action,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def list_for_tenant(db: Session, tenant_id: str, limit: int = 100) -> list[AuditLog]:
        return (
            db.query(AuditLog)
            .filter(AuditLog.tenant_id == tenant_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
