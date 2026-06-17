from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ObjectiveAnalysis:
    category: str
    complexity: str
    estimated_duration_hours: float
    success_probability: float
    predicted_risk_level: str
    selected_agents: list[str]
    dependencies: dict[str, Any]
    risks: list[dict[str, Any]]
    predicted_outputs: list[str]
    execution_roadmap: list[dict[str, Any]]
    blockers: list[str] = field(default_factory=list)


CATEGORY_PATTERNS: list[tuple[str, str]] = [
    (r"dashboard|visualization|power\s*bi|chart", "Analytics & Dashboards"),
    (r"pipeline|etl|ingest|data\s*flow", "Data Engineering"),
    (r"forecast|model|machine\s*learning|ml|predict", "Data Science & ML"),
    (r"web\s*app|application|api|backend|frontend", "Software Engineering"),
    (r"cloud|infrastructure|deploy|kubernetes|docker", "Cloud & Infrastructure"),
    (r"executive|summary|kpi|report|board", "Executive Reporting"),
    (r"operational|incident|retention|governance", "Operations & Governance"),
]


def classify_objective(title: str, description: str) -> str:
    text = f"{title} {description}".lower()
    for pattern, category in CATEGORY_PATTERNS:
        if re.search(pattern, text):
            return category
    return "Operations & Governance"


def estimate_complexity(title: str, description: str, agent_count: int) -> str:
    text = f"{title} {description}".lower()
    score = len(description.split()) // 20 + agent_count // 3
    if any(w in text for w in ("enterprise", "multi-tenant", "production", "compliance")):
        score += 2
    if any(w in text for w in ("simple", "basic", "quick")):
        score -= 1
    if score <= 2:
        return "low"
    if score <= 4:
        return "medium"
    if score <= 6:
        return "high"
    return "critical"


def detect_dependencies(title: str, description: str) -> dict[str, Any]:
    text = f"{title} {description}".lower()
    missing: list[str] = []
    if any(w in text for w in ("dashboard", "analytics", "report", "kpi")) and "data" not in text:
        missing.append("data_source")
    if "forecast" in text or "model" in text:
        missing.append("historical_data")
    if "deploy" in text or "cloud" in text:
        missing.append("infrastructure_credentials")
    if "pipeline" in text:
        missing.append("source_systems")
    return {
        "missing_data": [m for m in missing if "data" in m],
        "missing_resources": [m for m in missing if m not in ("data_source", "historical_data")],
        "missing_dependencies": missing,
        "resolved": len(missing) == 0,
    }


def detect_risks(title: str, description: str, dependencies: dict[str, Any]) -> list[dict[str, Any]]:
    text = f"{title} {description}".lower()
    risks: list[dict[str, Any]] = []

    if dependencies.get("missing_dependencies"):
        risks.append({
            "risk_type": "missing_dependencies",
            "severity": "high",
            "description": f"Missing: {', '.join(dependencies['missing_dependencies'])}",
            "mitigation": "Upload required datasets or connect data sources before execution.",
        })
    if any(w in text for w in ("pii", "customer", "personal", "health")):
        risks.append({
            "risk_type": "compliance",
            "severity": "high",
            "description": "Objective involves sensitive data — compliance review required.",
            "mitigation": "Enable governance agent and security review before deployment.",
        })
    if "production" in text:
        risks.append({
            "risk_type": "technical",
            "severity": "medium",
            "description": "Production deployment requires QA gate and approval.",
            "mitigation": "QA Engineer and approval workflow will be enforced.",
        })
    if not risks:
        risks.append({
            "risk_type": "operational",
            "severity": "low",
            "description": "Standard execution risk profile.",
            "mitigation": "Automated QA and evidence tracking enabled.",
        })
    return risks


def predict_outputs(category: str, title: str) -> list[str]:
    base = ["Execution evidence package", "Agent collaboration log"]
    mapping = {
        "Analytics & Dashboards": ["Interactive dashboard specification", "KPI definitions", "Data model"],
        "Data Engineering": ["ETL pipeline design", "Data quality report", "Schema documentation"],
        "Data Science & ML": ["Trained model specification", "Feature engineering report", "Performance metrics"],
        "Software Engineering": ["API specification", "Application architecture", "Test results"],
        "Cloud & Infrastructure": ["Infrastructure blueprint", "Deployment runbook", "Security checklist"],
        "Executive Reporting": ["Executive summary", "ROI analysis", "Strategic recommendations"],
        "Operations & Governance": ["Process improvement plan", "Risk assessment", "Compliance report"],
    }
    return base + mapping.get(category, ["Deliverable package", "Quality assurance report"])


def build_roadmap(selected_agents: list[str]) -> list[dict[str, Any]]:
    from nexus_one.workforce import get_agent_meta

    roadmap: list[dict[str, Any]] = []
    for idx, key in enumerate(selected_agents):
        meta = get_agent_meta(key) or {"name": key, "department": "unknown"}
        roadmap.append({
            "step": idx + 1,
            "agent_key": key,
            "agent_name": meta.get("name", key),
            "department": meta.get("department", "unknown"),
            "status": "pending",
        })
    return roadmap


def analyze_objective(title: str, description: str, selected_agents: list[str]) -> ObjectiveAnalysis:
    from nexus_one.workforce import select_agents_for_objective

    if not selected_agents:
        selected_agents = select_agents_for_objective(title, description)

    category = classify_objective(title, description)
    complexity = estimate_complexity(title, description, len(selected_agents))
    dependencies = detect_dependencies(title, description)
    risks = detect_risks(title, description, dependencies)

    duration_map = {"low": 4.0, "medium": 12.0, "high": 24.0, "critical": 48.0}
    duration = duration_map[complexity] * (1 + len(selected_agents) * 0.05)

    risk_penalty = sum(0.05 for r in risks if r["severity"] in ("high", "critical"))
    success_prob = max(0.55, min(0.98, 0.92 - risk_penalty - len(dependencies.get("missing_dependencies", [])) * 0.08))

    risk_levels = [r["severity"] for r in risks]
    predicted_risk = "critical" if "critical" in risk_levels else (
        "high" if "high" in risk_levels else ("medium" if "medium" in risk_levels else "low")
    )

    blockers = []
    if dependencies.get("missing_dependencies"):
        blockers.extend(dependencies["missing_dependencies"])

    return ObjectiveAnalysis(
        category=category,
        complexity=complexity,
        estimated_duration_hours=round(duration, 1),
        success_probability=round(success_prob * 100, 1),
        predicted_risk_level=predicted_risk,
        selected_agents=selected_agents,
        dependencies=dependencies,
        risks=risks,
        predicted_outputs=predict_outputs(category, title),
        execution_roadmap=build_roadmap(selected_agents),
        blockers=blockers,
    )
