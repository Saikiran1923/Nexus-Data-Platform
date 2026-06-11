from __future__ import annotations

from typing import Any, Dict, List

from agents.ai_data_engineer.agent import AiDataEngineerAgent
from agents.backend_engineer.agent import BackendEngineerAgent
from agents.cloud_engineer.agent import CloudEngineerAgent
from agents.data_analyst.agent import DataAnalystAgent
from agents.data_engineer.agent import DataEngineerAgent
from agents.data_governance.agent import DataGovernanceAgent
from agents.data_modeler.agent import DataModelerAgent
from agents.data_scientist.agent import DataScientistAgent
from agents.devops_engineer.agent import DevopsEngineerAgent
from agents.erp_specialist.agent import ErpSpecialistAgent
from agents.industry_specialist.agent import IndustrySpecialistAgent
from agents.master_data_management.agent import MasterDataManagementAgent
from agents.platform_engineer.agent import PlatformEngineerAgent
from agents.program_portfolio_manager.agent import ProgramPortfolioManagerAgent
from agents.python_developer.agent import PythonDeveloperAgent
from agents.qa_engineer.agent import QaEngineerAgent
from agents.security_engineer.agent import SecurityEngineerAgent
from agents.service_manager.agent import ServiceManagerAgent
from agents.capabilities import DOMAIN_KEYWORDS
from backend.models import AgentResult

# Agents that always participate in every task.
BASE_AGENTS: List[str] = ["data_engineer", "ai_data_engineer", "data_modeler"]

# Agents that always run at the end of every task (QA gate + deployment planning).
CLOSING_AGENTS: List[str] = ["qa_engineer", "devops_engineer"]


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
            # Enterprise domain agents.
            "program_portfolio_manager": ProgramPortfolioManagerAgent(),
            "service_manager": ServiceManagerAgent(),
            "data_governance": DataGovernanceAgent(),
            "master_data_management": MasterDataManagementAgent(),
            "backend_engineer": BackendEngineerAgent(),
            "cloud_engineer": CloudEngineerAgent(),
            "platform_engineer": PlatformEngineerAgent(),
            "security_engineer": SecurityEngineerAgent(),
            "erp_specialist": ErpSpecialistAgent(),
            "industry_specialist": IndustrySpecialistAgent(),
        }

    def select_agents(self, description: str) -> List[str]:
        text = description.lower()
        selected = list(BASE_AGENTS)

        for agent_key, keywords in DOMAIN_KEYWORDS.items():
            if agent_key not in self.registry:
                continue
            if any(word in text for word in keywords):
                selected.append(agent_key)

        selected.extend(CLOSING_AGENTS)
        return list(dict.fromkeys(selected))

    def run_agents(self, context: Dict[str, Any]) -> List[AgentResult]:
        selected_agents = context["selected_agents"]
        results: List[AgentResult] = []
        for agent_key in selected_agents:
            agent = self.registry[agent_key]
            results.append(agent.run(context))
        return results

    def list_agents(self) -> List[Dict[str, str]]:
        """Return metadata for every registered agent."""
        return [
            {"key": key, "name": agent.name, "role": agent.role}
            for key, agent in self.registry.items()
        ]
