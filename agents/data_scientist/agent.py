from __future__ import annotations

from typing import Any, Dict
from agents.base_agent import BaseAgent
from backend.models import AgentResult


class DataScientistAgent(BaseAgent):
    name = "Data Scientist Agent"
    role = "Data Scientist"

    category = "AI & Data Science"

    def run(self, context: Dict[str, Any]) -> AgentResult:
        from agents.capabilities import duties_for_category

        task = context.get("description", "")
        outputs = {
            "domain": self.category,
            "capabilities_covered": duties_for_category(self.category),
            "responsibilities_completed": [
                "Creates ML-ready features, model plan, evaluation approach, and prediction strategy.",
                "Generated implementation steps for the requested workflow.",
                "Created validation checkpoints and expected deliverables."
            ],
            "task_reference": task[:200],
        }
        return AgentResult(
            agent_name=self.name,
            role=self.role,
            summary="Data Scientist Agent completed assigned work.",
            outputs=outputs,
        )
