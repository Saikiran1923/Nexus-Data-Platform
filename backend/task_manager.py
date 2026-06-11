from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List

from agents.orchestrator.orchestrator import OrchestratorAgent
from backend.models import ApprovalRequest, TaskRecord, TaskRequest, TaskStatus


class TaskManager:
    def __init__(self) -> None:
        self.tasks: Dict[str, TaskRecord] = {}
        self.orchestrator = OrchestratorAgent()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_task(self, request: TaskRequest) -> TaskRecord:
        task_id = str(uuid.uuid4())
        now = self._now()
        record = TaskRecord(
            task_id=task_id,
            title=request.title,
            description=request.description,
            status=TaskStatus.CREATED,
            created_at=now,
            updated_at=now,
        )
        self.tasks[task_id] = record
        return record

    def run_task(self, task_id: str) -> TaskRecord:
        record = self.get_task(task_id)
        record.status = TaskStatus.RUNNING
        record.updated_at = self._now()

        selected_agents = self.orchestrator.select_agents(record.description)
        context = {
            "task_id": record.task_id,
            "title": record.title,
            "description": record.description,
            "selected_agents": selected_agents,
        }

        results = self.orchestrator.run_agents(context)
        qa_result = next((r for r in results if r.role == "QA/Test Engineer"), None)

        record.selected_agents = selected_agents
        record.results = results
        record.qa_passed = bool(qa_result and qa_result.outputs.get("qa_passed", False))
        record.status = TaskStatus.WAITING_FOR_APPROVAL if record.qa_passed else TaskStatus.FAILED
        record.updated_at = self._now()
        return record

    def approve_task(self, task_id: str, approval: ApprovalRequest) -> TaskRecord:
        record = self.get_task(task_id)

        if record.status != TaskStatus.WAITING_FOR_APPROVAL:
            raise ValueError("Task is not waiting for approval.")

        if approval.approved:
            record.human_approved = True
            record.status = TaskStatus.APPROVED
            record.deployment_message = "Human approved. Ready for deployment."
        else:
            record.human_approved = False
            record.status = TaskStatus.REJECTED
            record.deployment_message = f"Rejected by human reviewer. Comments: {approval.comments or 'No comments'}"

        record.updated_at = self._now()
        return record

    def deploy_task(self, task_id: str) -> TaskRecord:
        record = self.get_task(task_id)

        if record.status != TaskStatus.APPROVED or not record.human_approved:
            raise ValueError("Deployment blocked. Human approval is required.")

        record.status = TaskStatus.DEPLOYED
        record.deployment_message = "Deployment simulation completed successfully."
        record.updated_at = self._now()
        return record

    def get_task(self, task_id: str) -> TaskRecord:
        if task_id not in self.tasks:
            raise KeyError("Task not found.")
        return self.tasks[task_id]

    def list_tasks(self) -> List[TaskRecord]:
        return list(self.tasks.values())
