from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from backend.models import AgentResult, TaskStatus


class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    description: str = Field(..., min_length=5)
    dataset_name: Optional[str] = None
    selected_roles: Optional[List[str]] = None


class ApprovalRequest(BaseModel):
    approved: bool
    comments: Optional[str] = None


class TaskResponse(BaseModel):
    task_id: str
    tenant_id: str
    created_by: str
    title: str
    description: str
    status: TaskStatus
    selected_agents: List[str] = Field(default_factory=list)
    results: List[AgentResult] = Field(default_factory=list)
    qa_passed: bool = False
    human_approved: bool = False
    deployment_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class DatasetResponse(BaseModel):
    id: str
    tenant_id: str
    created_by: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    dataset_id: str | None
    original_filename: str
    file_size_bytes: int
    upload_status: str
    processing_status: str
    row_count: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UploadStatusResponse(BaseModel):
    id: str
    upload_status: str
    processing_status: str
    row_count: int | None
    error_message: str | None
    updated_at: datetime


class AuditLogResponse(BaseModel):
    id: str
    tenant_id: str | None
    user_id: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    details: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}
