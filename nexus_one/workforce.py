from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Enterprise AI workforce organized by department
WORKFORCE_DEPARTMENTS: dict[str, list[dict[str, Any]]] = {
    "executive": [
        {"key": "executive_summary", "name": "Executive Summary Agent", "role": "Executive Communications"},
        {"key": "business_impact", "name": "Business Impact Agent", "role": "Impact Analysis"},
    ],
    "strategy": [
        {"key": "planning", "name": "Planning Agent", "role": "Strategic Planning"},
        {"key": "research", "name": "Research Agent", "role": "Market & Domain Research"},
        {"key": "portfolio_manager", "name": "Portfolio Manager Agent", "role": "Portfolio Management"},
    ],
    "data": [
        {"key": "data_engineer", "name": "Data Engineer Agent", "role": "Data Engineering"},
        {"key": "data_analyst", "name": "Data Analyst Agent", "role": "Data Analytics"},
        {"key": "data_scientist", "name": "Data Scientist Agent", "role": "Data Science"},
        {"key": "data_modeler", "name": "Data Modeler Agent", "role": "Data Modeling"},
        {"key": "ai_data_engineer", "name": "AI Data Engineer Agent", "role": "AI Data Pipelines"},
    ],
    "engineering": [
        {"key": "python_developer", "name": "Python Developer Agent", "role": "Python Development"},
        {"key": "java_fullstack", "name": "Java Full Stack Developer Agent", "role": "Java Full Stack"},
        {"key": "backend_engineer", "name": "Backend Engineer Agent", "role": "Backend Engineering"},
        {"key": "platform_engineer", "name": "Platform Engineer Agent", "role": "Platform Engineering"},
    ],
    "analytics": [
        {"key": "power_bi", "name": "Power BI Developer Agent", "role": "Power BI Development"},
        {"key": "dashboard_intelligence", "name": "Dashboard Intelligence Agent", "role": "Dashboard Design"},
    ],
    "infrastructure": [
        {"key": "cloud_engineer", "name": "Cloud Engineer Agent", "role": "Cloud Infrastructure"},
        {"key": "devops_engineer", "name": "DevOps Engineer Agent", "role": "DevOps & CI/CD"},
        {"key": "security_engineer", "name": "Security Engineer Agent", "role": "Security Engineering"},
    ],
    "quality": [
        {"key": "qa_engineer", "name": "QA Engineer Agent", "role": "Quality Assurance"},
        {"key": "governance", "name": "Governance Agent", "role": "Data Governance"},
    ],
}

# Objective keyword → agent keys mapping for intelligent selection
OBJECTIVE_AGENT_MAP: dict[str, list[str]] = {
    "dashboard": ["planning", "data_engineer", "data_analyst", "dashboard_intelligence", "power_bi", "qa_engineer", "executive_summary"],
    "analytics": ["planning", "data_analyst", "data_scientist", "dashboard_intelligence", "executive_summary"],
    "sales": ["research", "data_analyst", "dashboard_intelligence", "executive_summary", "business_impact"],
    "kpi": ["planning", "data_analyst", "dashboard_intelligence", "executive_summary"],
    "forecast": ["planning", "data_scientist", "data_engineer", "qa_engineer", "executive_summary"],
    "retention": ["research", "data_scientist", "data_analyst", "business_impact", "executive_summary"],
    "operational": ["planning", "data_engineer", "data_analyst", "qa_engineer", "executive_summary"],
    "pipeline": ["planning", "data_engineer", "ai_data_engineer", "devops_engineer", "qa_engineer"],
    "web application": ["planning", "backend_engineer", "python_developer", "qa_engineer", "devops_engineer"],
    "cloud": ["planning", "cloud_engineer", "platform_engineer", "security_engineer", "devops_engineer"],
    "executive summary": ["research", "data_analyst", "executive_summary", "business_impact"],
    "report": ["planning", "data_analyst", "executive_summary", "business_impact"],
}

OBJECTIVE_CATEGORIES = [
    "Analytics & Dashboards",
    "Data Engineering",
    "Data Science & ML",
    "Software Engineering",
    "Cloud & Infrastructure",
    "Executive Reporting",
    "Operations & Governance",
]

EXECUTION_PHASES = [
    ("planning", 1),
    ("validation", 2),
    ("execution", 3),
    ("qa", 4),
    ("approval", 5),
    ("deployment", 6),
]


@dataclass
class WorkforceAgent:
    key: str
    name: str
    role: str
    department: str


def list_all_agents() -> list[WorkforceAgent]:
    agents: list[WorkforceAgent] = []
    for dept, members in WORKFORCE_DEPARTMENTS.items():
        for m in members:
            agents.append(WorkforceAgent(key=m["key"], name=m["name"], role=m["role"], department=dept))
    return agents


def get_agent_meta(key: str) -> dict[str, Any] | None:
    for dept, members in WORKFORCE_DEPARTMENTS.items():
        for m in members:
            if m["key"] == key:
                return {**m, "department": dept}
    return None


def select_agents_for_objective(title: str, description: str) -> list[str]:
    text = f"{title} {description}".lower()
    selected: list[str] = ["planning", "research"]

    for keyword, agents in OBJECTIVE_AGENT_MAP.items():
        if keyword in text:
            selected.extend(agents)

    if "security" in text or "compliance" in text:
        selected.append("security_engineer")
    if "governance" in text or "quality" in text:
        selected.append("governance")

    selected.extend(["qa_engineer", "executive_summary", "business_impact"])
    return list(dict.fromkeys(selected))
