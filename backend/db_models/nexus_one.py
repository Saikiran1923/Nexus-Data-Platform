from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from backend.db_models.base import Base, new_uuid, utcnow

_json = JSON().with_variant(JSONB(), "postgresql")


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    price_monthly_cents: Mapped[int] = mapped_column(Integer, default=0)
    runtime_minutes_day: Mapped[int] = mapped_column(Integer, default=5)
    max_agents: Mapped[int] = mapped_column(Integer, default=2)
    features: Mapped[list[str]] = mapped_column(_json, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TenantSubscription(Base):
    __tablename__ = "tenant_subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), unique=True)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscription_plans.id"))
    status: Mapped[str] = mapped_column(String(50), default="active")
    coupon_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan")


class Coupon(Base):
    __tablename__ = "coupons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)
    discount_value: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    trial_extension_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CouponRedemption(Base):
    __tablename__ = "coupon_redemptions"
    __table_args__ = (UniqueConstraint("coupon_id", "tenant_id", name="uq_coupon_tenant"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    coupon_id: Mapped[str] = mapped_column(String(36), ForeignKey("coupons.id"))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    redeemed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BusinessObjective(Base):
    __tablename__ = "business_objectives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    complexity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    success_probability: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    estimated_duration_hours: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    predicted_risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    execution_plan: Mapped[dict[str, Any] | None] = mapped_column(_json, nullable=True)
    selected_agents: Mapped[list[str] | None] = mapped_column(_json, nullable=True)
    dependencies: Mapped[dict[str, Any] | None] = mapped_column(_json, nullable=True)
    risks_detected: Mapped[list[dict[str, Any]] | None] = mapped_column(_json, nullable=True)
    predicted_outputs: Mapped[list[str] | None] = mapped_column(_json, nullable=True)
    business_impact: Mapped[dict[str, Any] | None] = mapped_column(_json, nullable=True)
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    current_phase: Mapped[str] = mapped_column(String(50), default="planning")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    objective_id: Mapped[str] = mapped_column(String(36), ForeignKey("business_objectives.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="planning")
    quality_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    hours_saved: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    cost_savings: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    revenue_impact: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ExecutionPhase(Base):
    __tablename__ = "execution_phases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    objective_id: Mapped[str] = mapped_column(String(36), ForeignKey("business_objectives.id", ondelete="CASCADE"))
    phase_name: Mapped[str] = mapped_column(String(50), nullable=False)
    phase_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    objective_id: Mapped[str] = mapped_column(String(36), ForeignKey("business_objectives.id", ondelete="CASCADE"))
    phase: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="info")
    agent_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    objective_id: Mapped[str] = mapped_column(String(36), ForeignKey("business_objectives.id", ondelete="CASCADE"))
    project_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    agent_key: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_metadata: Mapped[dict[str, Any] | None] = mapped_column(_json, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MemoryGraphNode(Base):
    __tablename__ = "memory_graph_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    objective_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("business_objectives.id", ondelete="SET NULL"), nullable=True)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(_json, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MemoryGraphEdge(Base):
    __tablename__ = "memory_graph_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"))
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("memory_graph_nodes.id", ondelete="CASCADE"))
    target_id: Mapped[str] = mapped_column(String(36), ForeignKey("memory_graph_nodes.id", ondelete="CASCADE"))
    relationship: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ObjectiveRisk(Base):
    __tablename__ = "objective_risks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"))
    objective_id: Mapped[str] = mapped_column(String(36), ForeignKey("business_objectives.id", ondelete="CASCADE"))
    risk_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    mitigation: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ExecutiveInsight(Base):
    __tablename__ = "executive_insights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"))
    objective_id: Mapped[str] = mapped_column(String(36), ForeignKey("business_objectives.id", ondelete="CASCADE"))
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    strategic_insights: Mapped[list[str] | None] = mapped_column(_json, nullable=True)
    recommendations: Mapped[list[str] | None] = mapped_column(_json, nullable=True)
    roi_analysis: Mapped[dict[str, Any] | None] = mapped_column(_json, nullable=True)
    impact_report: Mapped[dict[str, Any] | None] = mapped_column(_json, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RuntimeUsage(Base):
    __tablename__ = "runtime_usage"
    __table_args__ = (UniqueConstraint("tenant_id", "usage_date", name="uq_runtime_tenant_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"))
    usage_date: Mapped[datetime] = mapped_column(Date, default=lambda: utcnow().date())
    minutes_used: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
