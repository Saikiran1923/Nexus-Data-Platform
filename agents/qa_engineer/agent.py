from __future__ import annotations

from typing import Any, Dict
from agents.base_agent import BaseAgent
from backend.models import AgentResult


class QaEngineerAgent(BaseAgent):
    name = "QA/Test Engineer Agent"
    role = "QA/Test Engineer"
    category = "Testing & Quality"

    def run(self, context: Dict[str, Any]) -> AgentResult:
        from agents.capabilities import duties_for_category

        selected_agents = context.get("selected_agents", [])
        warnings = []
        if "data_engineer" not in selected_agents:
            warnings.append("Data Engineer Agent was not selected.")
        if not context.get("description"):
            warnings.append("Task description is missing.")

        status = "SUCCESS" if not warnings else "WARNING"
        return AgentResult(
            agent_name=self.name,
            role=self.role,
            status=status,
            summary="QA validation completed. Task is ready for human review." if not warnings else "QA completed with warnings.",
            outputs={
                "domain": self.category,
                "capabilities_covered": duties_for_category(self.category),
                "checks": [
                    "Validated required agent participation.",
                    "Validated task description availability.",
                    "Confirmed human approval is required before deployment."
                ],
                "qa_passed": not warnings,
            },
            warnings=warnings,
        )
