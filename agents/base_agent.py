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
