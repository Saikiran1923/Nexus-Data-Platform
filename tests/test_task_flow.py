from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_full_task_flow():
    create_response = client.post("/tasks", json={
        "title": "CSV to API Deployment",
        "description": "Upload CSV, clean data, create schema, analyze data, build API, test and deploy using Docker."
    })
    assert create_response.status_code == 200
    task = create_response.json()
    task_id = task["task_id"]

    run_response = client.post(f"/tasks/{task_id}/run")
    assert run_response.status_code == 200
    task = run_response.json()
    assert task["status"] == "WAITING_FOR_APPROVAL"
    assert task["qa_passed"] is True

    approval_response = client.post(f"/tasks/{task_id}/approval", json={
        "approved": True,
        "comments": "Approved after review."
    })
    assert approval_response.status_code == 200
    assert approval_response.json()["status"] == "APPROVED"

    deploy_response = client.post(f"/tasks/{task_id}/deploy")
    assert deploy_response.status_code == 200
    assert deploy_response.json()["status"] == "DEPLOYED"
