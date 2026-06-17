from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.auth.dependencies import CurrentUser
from backend.db_models.nexus_one import (
    BusinessObjective,
    Coupon,
    CouponRedemption,
    ExecutionPhase,
    ExecutiveInsight,
    ObjectiveRisk,
    Project,
    RuntimeUsage,
    SubscriptionPlan,
    TenantSubscription,
    TimelineEvent,
)
from backend.services.audit_service import AuditService
from nexus_one.evidence_engine import EvidenceEngine
from nexus_one.execution_engine import analyze_objective
from nexus_one.impact_engine import calculate_business_impact, generate_executive_summary, generate_roi_analysis
from nexus_one.memory_graph import MemoryGraph
from nexus_one.workforce import EXECUTION_PHASES as PHASES


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SubscriptionService:
    @staticmethod
    def seed_plans(db: Session) -> None:
        defaults = [
            ("Free", "free", 0, 5, 2, ["basic_objectives"]),
            ("Standard", "standard", 2900, 60, 5, ["basic_objectives", "workforce_board"]),
            ("Professional", "professional", 9900, 480, 99, ["mission_control", "executive_reports", "evidence_engine", "all_agents"]),
            ("Business", "business", 29900, 1440, 99, ["teams", "approvals", "audit_logs", "mission_control"]),
            ("Enterprise", "enterprise", 0, 99999, 99, ["custom_pricing", "sso", "dedicated_support"]),
        ]
        existing = {p.slug for p in db.query(SubscriptionPlan).all()}
        for name, slug, price, runtime, agents, features in defaults:
            if slug not in existing:
                db.add(SubscriptionPlan(
                    name=name, slug=slug, price_monthly_cents=price,
                    runtime_minutes_day=runtime, max_agents=agents, features=features,
                ))
        db.commit()

    @staticmethod
    def ensure_tenant_subscription(db: Session, tenant_id: str) -> TenantSubscription:
        sub = db.query(TenantSubscription).filter(TenantSubscription.tenant_id == tenant_id).first()
        if sub:
            return sub
        free_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.slug == "free").first()
        if not free_plan:
            SubscriptionService.seed_plans(db)
            free_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.slug == "free").first()
        sub = TenantSubscription(tenant_id=tenant_id, plan_id=free_plan.id, status="active")
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def get_plan_limits(db: Session, tenant_id: str) -> dict[str, Any]:
        sub = SubscriptionService.ensure_tenant_subscription(db, tenant_id)
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
        usage = (
            db.query(RuntimeUsage)
            .filter(RuntimeUsage.tenant_id == tenant_id, RuntimeUsage.usage_date == _utcnow().date())
            .first()
        )
        minutes_used = float(usage.minutes_used) if usage else 0.0
        return {
            "plan": plan.slug if plan else "free",
            "plan_name": plan.name if plan else "Free",
            "max_agents": plan.max_agents if plan else 2,
            "runtime_minutes_day": plan.runtime_minutes_day if plan else 5,
            "minutes_used_today": minutes_used,
            "minutes_remaining": max(0, (plan.runtime_minutes_day if plan else 5) - minutes_used),
            "features": plan.features if plan else [],
            "price_monthly_usd": (plan.price_monthly_cents / 100) if plan else 0,
        }

    @staticmethod
    def check_runtime_quota(db: Session, tenant_id: str, minutes_needed: float = 1.0) -> None:
        limits = SubscriptionService.get_plan_limits(db, tenant_id)
        if limits["minutes_remaining"] < minutes_needed:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Daily runtime limit reached ({limits['runtime_minutes_day']} min/day on {limits['plan_name']} plan)",
            )

    @staticmethod
    def record_runtime(db: Session, tenant_id: str, minutes: float) -> None:
        today = _utcnow().date()
        usage = (
            db.query(RuntimeUsage)
            .filter(RuntimeUsage.tenant_id == tenant_id, RuntimeUsage.usage_date == today)
            .first()
        )
        if usage:
            usage.minutes_used = float(usage.minutes_used) + minutes
        else:
            db.add(RuntimeUsage(tenant_id=tenant_id, usage_date=today, minutes_used=minutes))
        db.commit()


class CouponService:
    @staticmethod
    def seed_coupons(db: Session) -> None:
        from datetime import timedelta

        defaults = [
            ("WELCOME50", "50% off first month", "percentage", 50, None, 1000),
            ("STARTUP25", "25% off Standard plan", "percentage", 25, None, 500),
            ("EARLYACCESS", "30-day trial extension", "trial_extension", 0, 30, 200),
            ("INVESTORDEMO", "Investor demo trial", "trial_extension", 0, 30, 50),
        ]
        existing = {c.code for c in db.query(Coupon).all()}
        for code, desc, dtype, val, trial_days, max_uses in defaults:
            if code not in existing:
                db.add(Coupon(
                    code=code, description=desc, discount_type=dtype, discount_value=val,
                    trial_extension_days=trial_days, max_uses=max_uses,
                    expires_at=_utcnow() + timedelta(days=365),
                ))
        db.commit()

    @staticmethod
    def redeem(db: Session, current_user: CurrentUser, code: str) -> dict[str, Any]:
        coupon = db.query(Coupon).filter(Coupon.code == code.upper(), Coupon.is_active.is_(True)).first()
        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")
        if coupon.expires_at:
            expires = coupon.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < _utcnow():
                raise HTTPException(status_code=400, detail="Coupon expired")
        if coupon.max_uses and coupon.used_count >= coupon.max_uses:
            raise HTTPException(status_code=400, detail="Coupon usage limit reached")

        existing = (
            db.query(CouponRedemption)
            .filter(CouponRedemption.coupon_id == coupon.id, CouponRedemption.tenant_id == current_user.tenant_id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="Coupon already redeemed for this tenant")

        db.add(CouponRedemption(
            coupon_id=coupon.id, tenant_id=current_user.tenant_id, user_id=current_user.id,
        ))
        coupon.used_count += 1
        sub = SubscriptionService.ensure_tenant_subscription(db, current_user.tenant_id)
        sub.coupon_code = coupon.code
        if coupon.trial_extension_days:
            sub.current_period_end = _utcnow() + __import__("datetime").timedelta(days=coupon.trial_extension_days)
        db.commit()
        return {
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": float(coupon.discount_value),
            "trial_extension_days": coupon.trial_extension_days,
        }


class ObjectiveService:
    @staticmethod
    def create(
        db: Session,
        current_user: CurrentUser,
        *,
        title: str,
        description: str,
    ) -> BusinessObjective:
        SubscriptionService.check_runtime_quota(db, current_user.tenant_id, 0.5)
        limits = SubscriptionService.get_plan_limits(db, current_user.tenant_id)

        analysis = analyze_objective(title, description, [])
        if len(analysis.selected_agents) > limits["max_agents"]:
            analysis.selected_agents = analysis.selected_agents[: limits["max_agents"]]

        objective = BusinessObjective(
            tenant_id=current_user.tenant_id,
            created_by=current_user.id,
            title=title,
            description=description,
            category=analysis.category,
            complexity=analysis.complexity,
            status="analyzed",
            success_probability=analysis.success_probability,
            estimated_duration_hours=analysis.estimated_duration_hours,
            predicted_risk_level=analysis.predicted_risk_level,
            execution_plan={"roadmap": analysis.execution_roadmap},
            selected_agents=analysis.selected_agents,
            dependencies=analysis.dependencies,
            risks_detected=analysis.risks,
            predicted_outputs=analysis.predicted_outputs,
            current_phase="planning",
        )
        db.add(objective)
        db.flush()

        for phase_name, order in PHASES:
            db.add(ExecutionPhase(
                objective_id=objective.id, phase_name=phase_name, phase_order=order, status="pending",
            ))
        for risk in analysis.risks:
            db.add(ObjectiveRisk(
                tenant_id=current_user.tenant_id,
                objective_id=objective.id,
                risk_type=risk["risk_type"],
                severity=risk["severity"],
                description=risk["description"],
                mitigation=risk.get("mitigation"),
            ))

        db.add(TimelineEvent(
            objective_id=objective.id, phase="planning", event_type="objective_created",
            message=f"Business objective analyzed: {analysis.category} ({analysis.complexity} complexity)",
            status="success",
        ))

        MemoryGraph.store(
            db, tenant_id=current_user.tenant_id, objective_id=objective.id,
            node_type="objective", title=title,
            content={"description": description, "category": analysis.category, "analysis": analysis.__dict__},
        )

        db.commit()
        db.refresh(objective)
        AuditService.log(
            db, action="objective_create", user_id=current_user.id, tenant_id=current_user.tenant_id,
            resource_type="business_objective", resource_id=objective.id,
        )
        return objective

    @staticmethod
    def get(db: Session, current_user: CurrentUser, objective_id: str) -> BusinessObjective:
        obj = (
            db.query(BusinessObjective)
            .filter(BusinessObjective.id == objective_id, BusinessObjective.tenant_id == current_user.tenant_id)
            .first()
        )
        if not obj:
            raise HTTPException(status_code=404, detail="Objective not found")
        return obj

    @staticmethod
    def list_for_tenant(db: Session, current_user: CurrentUser) -> list[BusinessObjective]:
        return (
            db.query(BusinessObjective)
            .filter(BusinessObjective.tenant_id == current_user.tenant_id)
            .order_by(BusinessObjective.created_at.desc())
            .all()
        )
