from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth.dependencies import ROLE_ADMIN, ROLE_DEVELOPER, ROLE_USER, CurrentUser, require_roles
from backend.database.session import get_db
from backend.schemas.common import APIResponse
from backend.schemas.nexus_one import CouponRedeemRequest, SubscriptionPlanResponse
from backend.services.nexus_one_service import CouponService, SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/plans", response_model=APIResponse[list])
def list_plans(db: Session = Depends(get_db)) -> APIResponse[list]:
    from backend.db_models.nexus_one import SubscriptionPlan

    SubscriptionService.seed_plans(db)
    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active.is_(True)).all()
    return APIResponse(data=[
        {"slug": p.slug, "name": p.name, "price_monthly_usd": p.price_monthly_cents / 100,
         "runtime_minutes_day": p.runtime_minutes_day, "max_agents": p.max_agents, "features": p.features}
        for p in plans
    ])


@router.get("/current", response_model=APIResponse[SubscriptionPlanResponse])
def current_plan(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_USER)),
) -> APIResponse[SubscriptionPlanResponse]:
    limits = SubscriptionService.get_plan_limits(db, current_user.tenant_id)
    return APIResponse(data=SubscriptionPlanResponse(**limits))


@router.post("/coupons/redeem", response_model=APIResponse[dict])
def redeem_coupon(
    payload: CouponRedeemRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_DEVELOPER, ROLE_USER)),
) -> APIResponse[dict]:
    result = CouponService.redeem(db, current_user, payload.code)
    return APIResponse(message="Coupon redeemed", data=result)
