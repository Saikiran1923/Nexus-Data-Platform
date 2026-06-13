def test_full_task_flow(client, auth_headers):
    create_response = client.post(
        "/api/v1/tasks",
        json={
            "title": "CSV to API Deployment",
            "description": "Upload CSV, clean data, create schema, analyze data, build API, test and deploy using Docker.",
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 200
    task = create_response.json()["data"]
    task_id = task["task_id"]

    run_response = client.post(f"/api/v1/tasks/{task_id}/run", headers=auth_headers)
    assert run_response.status_code == 200
    task = run_response.json()["data"]
    assert task["status"] == "WAITING_FOR_APPROVAL"
    assert task["qa_passed"] is True

    approval_response = client.post(
        f"/api/v1/tasks/{task_id}/approval",
        json={"approved": True, "comments": "Approved after review."},
        headers=auth_headers,
    )
    assert approval_response.status_code == 200
    assert approval_response.json()["data"]["status"] == "APPROVED"

    deploy_response = client.post(f"/api/v1/tasks/{task_id}/deploy", headers=auth_headers)
    assert deploy_response.status_code == 200
    assert deploy_response.json()["data"]["status"] == "DEPLOYED"
