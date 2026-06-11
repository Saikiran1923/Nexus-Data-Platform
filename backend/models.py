from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    APPROVED = "APPROVED"
    DEPLOYED = "DEPLOYED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class AgentResult(BaseModel):
    agent_name: str
    role: str
    status: str = "SUCCESS"
    summary: str
    outputs: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class TaskRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    description: str = Field(..., min_length=5)
    dataset_name: Optional[str] = None

    # User-selected agents/roles
    selected_roles: Optional[List[str]] = Field(default=None)


class TaskRecord(BaseModel):
    task_id: str
    title: str
    description: str

    status: TaskStatus

    # Selected agents for execution
    selected_agents: List[str] = Field(default_factory=list)

    # Agent execution results
    results: List[AgentResult] = Field(default_factory=list)

    qa_passed: bool = False
    human_approved: bool = False

    deployment_message: Optional[str] = None

    created_at: str
    updated_at: str


class ApprovalRequest(BaseModel):
    approved: bool
    comments: Optional[str] = None