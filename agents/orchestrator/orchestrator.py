from __future__ import annotations

from typing import Any, Dict, List

from agents.ai_data_engineer.agent import AiDataEngineerAgent
from agents.data_analyst.agent import DataAnalystAgent
from agents.data_engineer.agent import DataEngineerAgent
from agents.data_modeler.agent import DataModelerAgent
from agents.data_scientist.agent import DataScientistAgent
from agents.devops_engineer.agent import DevopsEngineerAgent
from agents.python_developer.agent import PythonDeveloperAgent
from agents.qa_engineer.agent import QaEngineerAgent
from backend.models import AgentResult


class OrchestratorAgent:
    name = "AI Orchestrator Agent"
    role = "AI Orchestrator"

    def __init__(self) -> None:
        self.registry = {
            "data_engineer": DataEngineerAgent(),
            "ai_data_engineer": AiDataEngineerAgent(),
            "data_scientist": DataScientistAgent(),
            "data_analyst": DataAnalystAgent(),
            "data_modeler": DataModelerAgent(),
            "python_developer": PythonDeveloperAgent(),
            "qa_engineer": QaEngineerAgent(),
            "devops_engineer": DevopsEngineerAgent(),
        }

    def select_agents(self, description: str) -> List[str]:
        text = description.lower()
        selected = ["data_engineer", "ai_data_engineer", "data_modeler"]

        keyword_map = {
            "data_scientist": ["model", "prediction", "machine learning", "ml", "forecast", "classification"],
            "data_analyst": ["dashboard", "report", "kpi", "insight", "analysis", "visual"],
            "python_developer": ["api", "backend", "fastapi", "service", "endpoint", "script"],
            "devops_engineer": ["deploy", "docker", "kubernetes", "ci/cd", "release"],
        }

        for agent, keywords in keyword_map.items():
            if any(word in text for word in keywords):
                selected.append(agent)

        selected.extend(["qa_engineer", "devops_engineer"])
        return list(dict.fromkeys(selected))

    def run_agents(self, context: Dict[str, Any]) -> List[AgentResult]:
        selected_agents = context["selected_agents"]
        results: List[AgentResult] = []
        for agent_key in selected_agents:
            agent = self.registry[agent_key]
            results.append(agent.run(context))
        return results
