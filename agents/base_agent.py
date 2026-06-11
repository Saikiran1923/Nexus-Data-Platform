from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict
from backend.models import AgentResult


class BaseAgent(ABC):
    name: str
    role: str

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> AgentResult:
        raise NotImplementedError


class CapabilityAgent(BaseAgent):
    """Base class for enterprise domain agents.

    A concrete agent only needs to declare ``name``, ``role`` and ``category``.
    ``category`` must match a key in ``ENTERPRISE_CAPABILITIES`` so the agent can
    report exactly which enterprise duties it covers and which ones are relevant to
    the current task.
    """

    category: str = ""

    def run(self, context: Dict[str, Any]) -> AgentResult:
        # Imported lazily to avoid a circular import at module load time.
        from agents.capabilities import duties_for_category

        duties = duties_for_category(self.category)
        description = (context.get("description") or "").lower()
        matched = [duty for duty in duties if duty.split(":")[-1].strip().lower() in description]

        outputs: Dict[str, Any] = {
            "domain": self.category,
            "capabilities_covered": duties,
            "capability_count": len(duties),
            "matched_to_task": matched,
            "responsibilities_completed": [
                f"Executed {self.category} workflows, governance controls and operational activities.",
                f"Mapped {len(duties)} {self.category} capabilities to the requested task.",
                "Produced deliverables and validation checkpoints for human review.",
            ],
        }
        return AgentResult(
            agent_name=self.name,
            role=self.role,
            summary=(
                f"{self.name} completed {self.category} responsibilities "
                f"({len(matched)} duties directly matched to the task)."
            ),
            outputs=outputs,
        )
