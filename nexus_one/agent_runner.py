from __future__ import annotations

from typing import Any

from backend.models import AgentResult
from nexus_one.workforce import get_agent_meta

# Map workforce keys to existing orchestrator agents
ORCHESTRATOR_MAP: dict[str, str] = {
    "data_engineer": "data_engineer",
    "data_analyst": "data_analyst",
    "data_scientist": "data_scientist",
    "data_modeler": "data_modeler",
    "ai_data_engineer": "ai_data_engineer",
    "python_developer": "python_developer",
    "backend_engineer": "backend_engineer",
    "platform_engineer": "platform_engineer",
    "cloud_engineer": "cloud_engineer",
    "devops_engineer": "devops_engineer",
    "security_engineer": "security_engineer",
    "qa_engineer": "qa_engineer",
    "governance": "data_governance",
    "portfolio_manager": "program_portfolio_manager",
}


class NexusWorkforceAgent:
    """Lightweight agent for Nexus One workforce roles not in legacy orchestrator."""

    def __init__(self, key: str) -> None:
        self.key = key
        meta = get_agent_meta(key) or {"name": key, "role": key}
        self.name = meta["name"]
        self.role = meta["role"]
        self.department = meta.get("department", "executive")

    def run(self, context: dict[str, Any], shared_memory: dict[str, Any]) -> AgentResult:
        objective = context.get("title", "Business Objective")
        prior_outputs = shared_memory.get("agent_outputs", [])

        actions = {
            "executive_summary": ("Generated executive summary", f"Synthesized findings from {len(prior_outputs)} prior agents"),
            "business_impact": ("Calculated business impact", "Quantified hours saved, cost savings, and ROI"),
            "planning": ("Created execution plan", f"Defined roadmap for: {objective}"),
            "research": ("Completed domain research", "Analyzed market context and best practices"),
            "power_bi": ("Designed Power BI dashboard", "Created data model and visualization specification"),
            "dashboard_intelligence": ("Built dashboard intelligence layer", "Defined KPIs and drill-down paths"),
            "java_fullstack": ("Designed full-stack architecture", "Java/Spring backend with React frontend spec"),
        }
        action, output = actions.get(self.key, (f"Executed {self.role}", f"Completed {self.role} deliverables"))

        result_outputs: dict[str, Any] = {
            "action": action,
            "deliverable": output,
            "department": self.department,
            "shared_memory_used": len(prior_outputs),
        }

        if self.key == "executive_summary" and prior_outputs:
            result_outputs["synthesis"] = [o.get("summary", "") for o in prior_outputs[-5:]]

        return AgentResult(
            agent_name=self.name,
            role=self.role,
            summary=f"{self.name}: {action}",
            outputs=result_outputs,
        )


def run_workforce_agent(
    agent_key: str,
    context: dict[str, Any],
    shared_memory: dict[str, Any],
) -> AgentResult:
    if agent_key in ORCHESTRATOR_MAP:
        from agents.orchestrator.orchestrator import OrchestratorAgent

        orchestrator = OrchestratorAgent()
        legacy_key = ORCHESTRATOR_MAP[agent_key]
        if legacy_key in orchestrator.registry:
            ctx = {**context, "selected_agents": [legacy_key], "description": context.get("description", "")}
            return orchestrator.registry[legacy_key].run(ctx)

    agent = NexusWorkforceAgent(agent_key)
    return agent.run(context, shared_memory)
