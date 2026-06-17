from __future__ import annotations

from typing import Any


def calculate_business_impact(
    *,
    complexity: str,
    agent_count: int,
    duration_hours: float,
    quality_score: float,
    category: str,
) -> dict[str, Any]:
    """Calculate business impact metrics from execution parameters."""
    complexity_multiplier = {"low": 1.0, "medium": 2.5, "high": 5.0, "critical": 8.0}
    mult = complexity_multiplier.get(complexity, 2.0)

    hours_saved = round(duration_hours * 3.5 * mult, 1)
    hourly_rate = 85.0
    cost_savings = round(hours_saved * hourly_rate, 2)
    productivity_gain = round(min(95.0, 40 + agent_count * 5 + quality_score * 0.3), 1)
    quality_improvement = round(quality_score, 1)
    risk_reduction = round(min(90.0, 30 + quality_score * 0.5 + agent_count * 2), 1)
    revenue_impact = round(cost_savings * 1.8, 2) if category in (
        "Analytics & Dashboards", "Executive Reporting", "Data Science & ML"
    ) else round(cost_savings * 0.6, 2)

    return {
        "hours_saved": hours_saved,
        "cost_savings_usd": cost_savings,
        "productivity_gain_pct": productivity_gain,
        "quality_improvement_pct": quality_improvement,
        "risk_reduction_pct": risk_reduction,
        "revenue_impact_usd": revenue_impact,
        "roi_multiple": round(revenue_impact / max(cost_savings, 1) * 2, 2),
    }


def generate_executive_summary(
    title: str,
    category: str,
    impact: dict[str, Any],
    agent_names: list[str],
    evidence_count: int,
) -> str:
    return (
        f"Nexus One successfully executed the business objective: \"{title}\".\n\n"
        f"Category: {category}\n"
        f"AI Workforce: {len(agent_names)} agents collaborated across {evidence_count} traceable actions.\n\n"
        f"Business Impact:\n"
        f"• {impact['hours_saved']} hours saved\n"
        f"• ${impact['cost_savings_usd']:,.0f} estimated cost savings\n"
        f"• {impact['productivity_gain_pct']}% productivity gain\n"
        f"• {impact['quality_improvement_pct']}% quality improvement\n"
        f"• ${impact['revenue_impact_usd']:,.0f} potential revenue impact\n\n"
        f"Recommendation: Deploy outputs to production and schedule quarterly review."
    )


def generate_roi_analysis(impact: dict[str, Any], plan_cost_monthly: float = 99.0) -> dict[str, Any]:
    annual_savings = impact["cost_savings_usd"] * 12
    annual_cost = plan_cost_monthly * 12
    return {
        "annual_savings_usd": round(annual_savings, 2),
        "annual_platform_cost_usd": annual_cost,
        "net_annual_benefit_usd": round(annual_savings - annual_cost, 2),
        "roi_percentage": round((annual_savings - annual_cost) / max(annual_cost, 1) * 100, 1),
        "payback_period_months": round(annual_cost / max(impact["cost_savings_usd"], 1), 1),
    }
