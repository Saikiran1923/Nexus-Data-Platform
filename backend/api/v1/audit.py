from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth.dependencies import ROLE_ADMIN, ROLE_REVIEWER, CurrentUser, require_roles
from backend.database.session import get_db
from backend.schemas.api import AuditLogResponse
from backend.schemas.common import APIResponse
from backend.services.audit_service import AuditService

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=APIResponse[list[AuditLogResponse]])
def list_audit_logs(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_REVIEWER)),
    limit: int = 100,
) -> APIResponse[list[AuditLogResponse]]:
    logs = AuditService.list_for_tenant(db, current_user.tenant_id, limit=min(limit, 500))
    return APIResponse(data=[AuditLogResponse.model_validate(log) for log in logs])
