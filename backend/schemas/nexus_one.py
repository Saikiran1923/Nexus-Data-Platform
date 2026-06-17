from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ObjectiveCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)


class ObjectiveResponse(BaseModel):
    id: str
    tenant_id: str
    created_by: str
    title: str
    description: str
    category: Optional[str]
    complexity: Optional[str]
    status: str
    success_probability: Optional[float]
    estimated_duration_hours: Optional[float]
    predicted_risk_level: Optional[str]
    execution_plan: Optional[dict[str, Any]]
    selected_agents: Optional[List[str]]
    dependencies: Optional[dict[str, Any]]
    risks_detected: Optional[List[dict[str, Any]]]
    predicted_outputs: Optional[List[str]]
    business_impact: Optional[dict[str, Any]]
    executive_summary: Optional[str]
    quality_score: Optional[float]
    current_phase: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvidenceResponse(BaseModel):
    id: str
    objective_id: str
    agent_key: str
    agent_name: str
    action: str
    input_summary: Optional[str]
    output_summary: Optional[str]
    reason: Optional[str]
    impact: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class TimelineEventResponse(BaseModel):
    id: str
    phase: str
    event_type: str
    message: str
    status: str
    agent_key: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class MissionControlDashboard(BaseModel):
    kpis: dict[str, Any]
    subscription: dict[str, Any]
    open_risks: int
    recent_objectives: List[dict[str, Any]]


class CouponRedeemRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)


class SubscriptionPlanResponse(BaseModel):
    plan: str
    plan_name: str
    max_agents: int
    runtime_minutes_day: int
    minutes_used_today: float
    minutes_remaining: float
    features: List[str]
    price_monthly_usd: float
