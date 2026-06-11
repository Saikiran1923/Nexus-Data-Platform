from fastapi.testclient import TestClient

from agents.capabilities import (
    CATEGORY_AGENTS,
    ENTERPRISE_CAPABILITIES,
    duties_for_category,
    total_capability_count,
)
from agents.orchestrator.orchestrator import OrchestratorAgent
from backend.main import app

client = TestClient(app)

# Expected duty counts per category, derived directly from the enterprise duty list.
EXPECTED_COUNTS = {
    "Program & Portfolio Management": 20,
    "Service Management": 17,
    "Data Governance": 16,
    "Master Data Management": 12,
    "Data Engineering": 21,
    "Data Analytics": 18,
    "AI & Data Science": 20,
    "Backend Engineering": 14,
    "Cloud Engineering": 31,
    "DevOps & Platform Engineering": 19,
    "Security": 15,
    "Testing & Quality": 14,
    "SAP / ERP": 16,
    "Industries": 28,
}


def test_catalog_has_all_categories():
    assert set(ENTERPRISE_CAPABILITIES.keys()) == set(EXPECTED_COUNTS.keys())


def test_duty_counts_match_expected():
    for category, expected in EXPECTED_COUNTS.items():
        assert len(duties_for_category(category)) == expected, category
    assert total_capability_count() == sum(EXPECTED_COUNTS.values())


def test_every_category_has_registered_owning_agent():
    orchestrator = OrchestratorAgent()
    for category, agent_key in CATEGORY_AGENTS.items():
        assert agent_key in orchestrator.registry, category


def test_capabilities_endpoint():
    response = client.get("/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["total_categories"] == len(EXPECTED_COUNTS)
    assert data["total_capabilities"] == sum(EXPECTED_COUNTS.values())
    returned = {c["category"]: c["duty_count"] for c in data["categories"]}
    assert returned == EXPECTED_COUNTS


def test_capability_category_endpoint_case_insensitive():
    response = client.get("/capabilities/security")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "Security"
    assert "Zero Trust" in data["duties"]


def test_capability_category_endpoint_unknown():
    assert client.get("/capabilities/does-not-exist").status_code == 404


def test_agents_endpoint_lists_all_agents():
    response = client.get("/agents")
    assert response.status_code == 200
    data = response.json()
    assert data["total_agents"] == 18
    keys = {a["key"] for a in data["agents"]}
    for agent_key in CATEGORY_AGENTS.values():
        assert agent_key in keys


def test_orchestrator_routes_enterprise_keywords():
    orchestrator = OrchestratorAgent()
    description = (
        "Manage the program portfolio and PMO governance, handle incident and "
        "change management with SLA tracking, enforce data governance lineage and "
        "MDM customer master, build REST and GraphQL microservices, deploy on AWS "
        "Redshift and Azure Synapse, use Terraform GitOps on Kubernetes, apply "
        "zero trust IAM encryption, integrate SAP S/4HANA and Salesforce, for a "
        "healthcare and banking client."
    )
    selected = orchestrator.select_agents(description)
    for expected in [
        "program_portfolio_manager",
        "service_manager",
        "data_governance",
        "master_data_management",
        "backend_engineer",
        "cloud_engineer",
        "platform_engineer",
        "security_engineer",
        "erp_specialist",
        "industry_specialist",
    ]:
        assert expected in selected, expected


def test_enterprise_task_flow_reaches_deployment():
    create = client.post("/tasks", json={
        "title": "Enterprise DataOps Program",
        "description": (
            "Run a SAP S/4HANA data migration with data governance, MDM, AWS and "
            "Azure cloud pipelines, security controls, incident management and "
            "executive dashboards for a banking client."
        ),
    })
    assert create.status_code == 200
    task_id = create.json()["task_id"]

    run = client.post(f"/tasks/{task_id}/run")
    assert run.status_code == 200
    assert run.json()["status"] == "WAITING_FOR_APPROVAL"
    assert run.json()["qa_passed"] is True

    approve = client.post(f"/tasks/{task_id}/approval", json={"approved": True})
    assert approve.status_code == 200
    assert approve.json()["status"] == "APPROVED"

    deploy = client.post(f"/tasks/{task_id}/deploy")
    assert deploy.status_code == 200
    assert deploy.json()["status"] == "DEPLOYED"
