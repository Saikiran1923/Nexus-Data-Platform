"""Test Nexus One objective flow and mission control."""


def test_create_objective_analyzed(client, auth_headers):
    response = client.post(
        "/api/v1/objectives",
        json={
            "title": "Build Customer Analytics Dashboard",
            "description": "Create an executive dashboard with customer KPIs, retention metrics, and revenue analytics.",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "Build Customer Analytics Dashboard"
    assert data["status"] == "analyzed"
    assert data["category"] == "Analytics & Dashboards"
    assert data["selected_agents"]
    assert data["success_probability"] > 0


def test_execute_objective_completes(client, auth_headers):
    create = client.post(
        "/api/v1/objectives",
        json={
            "title": "Create Executive KPI Report",
            "description": "Generate executive KPI report with sales performance and forecasting insights.",
        },
        headers=auth_headers,
    )
    objective_id = create.json()["data"]["id"]

    execute = client.post(f"/api/v1/objectives/{objective_id}/execute", headers=auth_headers)
    assert execute.status_code == 200

    detail = client.get(f"/api/v1/objectives/{objective_id}", headers=auth_headers)
    assert detail.json()["data"]["status"] == "completed"
    assert detail.json()["data"]["executive_summary"]
    assert detail.json()["data"]["business_impact"]


def test_mission_control_dashboard(client, auth_headers):
    response = client.get("/api/v1/mission-control/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "kpis" in data
    assert "business_objectives" in data["kpis"]
    assert "subscription" in data


def test_workforce_board(client, auth_headers):
    response = client.get("/api/v1/mission-control/workforce", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_agents"] >= 20
    assert "executive" in data["departments"]


def test_evidence_after_execution(client, auth_headers):
    create = client.post(
        "/api/v1/objectives",
        json={
            "title": "Analyze Sales Performance",
            "description": "Analyze quarterly sales data and produce actionable insights for leadership.",
        },
        headers=auth_headers,
    )
    objective_id = create.json()["data"]["id"]
    client.post(f"/api/v1/objectives/{objective_id}/execute", headers=auth_headers)

    evidence = client.get("/api/v1/mission-control/evidence", headers=auth_headers)
    assert evidence.status_code == 200
    assert len(evidence.json()["data"]) > 0


def test_subscription_plans(client):
    response = client.get("/api/v1/subscriptions/plans")
    assert response.status_code == 200
    plans = response.json()["data"]
    slugs = {p["slug"] for p in plans}
    assert "free" in slugs
    assert "professional" in slugs


def test_coupon_redeem(client, auth_headers):
    response = client.post(
        "/api/v1/subscriptions/coupons/redeem",
        json={"code": "WELCOME50"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["code"] == "WELCOME50"
