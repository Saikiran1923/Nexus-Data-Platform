from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from agents.orchestrator.orchestrator import OrchestratorAgent
from backend.auth.dependencies import CurrentUser
from backend.db_models.task import Task
from backend.models import AgentResult, TaskStatus
from backend.schemas.api import ApprovalRequest, TaskCreateRequest, TaskResponse
from backend.services.audit_service import AuditService

_orchestrator = OrchestratorAgent()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_agent_results(results: list[AgentResult]) -> list[dict[str, Any]]:
    return [r.model_dump() for r in results]


def _deserialize_agent_results(data: list[dict[str, Any]] | None) -> list[AgentResult]:
    if not data:
        return []
    return [AgentResult.model_validate(item) for item in data]


def task_to_response(task: Task) -> TaskResponse:
    return TaskResponse(
        task_id=task.id,
        tenant_id=task.tenant_id,
        created_by=task.created_by,
        title=task.title,
        description=task.description,
        status=TaskStatus(task.status),
        selected_agents=task.selected_agents or [],
        results=_deserialize_agent_results(task.results),
        qa_passed=task.qa_passed,
        human_approved=task.human_approved,
        deployment_message=task.deployment_message,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


class TaskService:
    @staticmethod
    def create(
        db: Session,
        current_user: CurrentUser,
        request: TaskCreateRequest,
        ip_address: str | None = None,
    ) -> TaskResponse:
        task = Task(
            tenant_id=current_user.tenant_id,
            created_by=current_user.id,
            title=request.title,
            description=request.description,
            status=TaskStatus.CREATED.value,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        AuditService.log(
            db,
            action="task_create",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            resource_type="task",
            resource_id=task.id,
            ip_address=ip_address,
        )
        return task_to_response(task)

    @staticmethod
    def list_for_tenant(db: Session, current_user: CurrentUser) -> list[TaskResponse]:
        tasks = (
            db.query(Task)
            .filter(Task.tenant_id == current_user.tenant_id)
            .order_by(Task.created_at.desc())
            .all()
        )
        return [task_to_response(t) for t in tasks]

    @staticmethod
    def get(db: Session, current_user: CurrentUser, task_id: str) -> TaskResponse:
        task = (
            db.query(Task)
            .filter(Task.id == task_id, Task.tenant_id == current_user.tenant_id)
            .first()
        )
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        AuditService.log(
            db,
            action="data_access",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            resource_type="task",
            resource_id=task.id,
        )
        return task_to_response(task)

    @staticmethod
    def run(db: Session, current_user: CurrentUser, task_id: str, ip_address: str | None = None) -> TaskResponse:
        task = (
            db.query(Task)
            .filter(Task.id == task_id, Task.tenant_id == current_user.tenant_id)
            .first()
        )
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        task.status = TaskStatus.RUNNING.value
        task.updated_at = _utcnow()

        selected_agents = _orchestrator.select_agents(task.description)
        context = {
            "task_id": task.id,
            "title": task.title,
            "description": task.description,
            "selected_agents": selected_agents,
        }
        results = _orchestrator.run_agents(context)
        qa_result = next((r for r in results if r.role == "QA/Test Engineer"), None)

        task.selected_agents = selected_agents
        task.results = _serialize_agent_results(results)
        task.qa_passed = bool(qa_result and qa_result.outputs.get("qa_passed", False))
        task.status = (
            TaskStatus.WAITING_FOR_APPROVAL.value if task.qa_passed else TaskStatus.FAILED.value
        )
        task.updated_at = _utcnow()
        db.commit()
        db.refresh(task)

        AuditService.log(
            db,
            action="task_run",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            resource_type="task",
            resource_id=task.id,
            details={"status": task.status},
            ip_address=ip_address,
        )
        return task_to_response(task)

    @staticmethod
    def approve(
        db: Session,
        current_user: CurrentUser,
        task_id: str,
        approval: ApprovalRequest,
        ip_address: str | None = None,
    ) -> TaskResponse:
        task = (
            db.query(Task)
            .filter(Task.id == task_id, Task.tenant_id == current_user.tenant_id)
            .first()
        )
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        if task.status != TaskStatus.WAITING_FOR_APPROVAL.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task is not waiting for approval")

        if approval.approved:
            task.human_approved = True
            task.status = TaskStatus.APPROVED.value
            task.deployment_message = "Human approved. Ready for deployment."
        else:
            task.human_approved = False
            task.status = TaskStatus.REJECTED.value
            task.deployment_message = (
                f"Rejected by human reviewer. Comments: {approval.comments or 'No comments'}"
            )

        task.updated_at = _utcnow()
        db.commit()
        db.refresh(task)

        AuditService.log(
            db,
            action="pipeline_approval",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            resource_type="task",
            resource_id=task.id,
            details={"approved": approval.approved},
            ip_address=ip_address,
        )
        return task_to_response(task)

    @staticmethod
    def deploy(db: Session, current_user: CurrentUser, task_id: str, ip_address: str | None = None) -> TaskResponse:
        task = (
            db.query(Task)
            .filter(Task.id == task_id, Task.tenant_id == current_user.tenant_id)
            .first()
        )
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        if task.status != TaskStatus.APPROVED.value or not task.human_approved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deployment blocked. Human approval is required.",
            )

        task.status = TaskStatus.DEPLOYED.value
        task.deployment_message = "Deployment simulation completed successfully."
        task.updated_at = _utcnow()
        db.commit()
        db.refresh(task)

        AuditService.log(
            db,
            action="task_deploy",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            resource_type="task",
            resource_id=task.id,
            ip_address=ip_address,
        )
        return task_to_response(task)
