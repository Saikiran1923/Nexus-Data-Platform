from __future__ import annotations

import io
from pathlib import Path

import pytest


def test_signup_and_login(client):
    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "owner@corp.com",
            "password": "password123",
            "tenant_name": "Corp",
            "tenant_slug": "corp",
        },
    )
    assert signup.status_code == 200
    assert "access_token" in signup.json()["data"]

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@corp.com", "password": "password123", "tenant_slug": "corp"},
    )
    assert login.status_code == 200
    assert login.json()["data"]["token_type"] == "bearer"


def test_protected_route_requires_auth(client):
    response = client.get("/api/v1/tasks")
    assert response.status_code == 401


def test_csv_upload_and_processing(client, auth_headers):
    csv_content = b"name,email\nAlice,alice@example.com\nBob,bob@example.com\n"
    response = client.post(
        "/api/v1/uploads",
        files=[("files", ("customers.csv", io.BytesIO(csv_content), "text/csv"))],
        headers=auth_headers,
    )
    assert response.status_code == 200
    uploads = response.json()["data"]
    assert len(uploads) == 1
    upload_id = uploads[0]["id"]
    assert uploads[0]["upload_status"] == "completed"

    status_response = client.get(f"/api/v1/uploads/{upload_id}/status", headers=auth_headers)
    assert status_response.status_code == 200
    status_data = status_response.json()["data"]
    assert status_data["processing_status"] == "completed"
    assert status_data["row_count"] == 2


def test_tenant_isolation(client, auth_headers):
    create = client.post(
        "/api/v1/tasks",
        json={"title": "Tenant A Task", "description": "Isolated task for tenant A testing."},
        headers=auth_headers,
    )
    task_id = create.json()["data"]["task_id"]

    other_signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "other@example.com",
            "password": "password123",
            "tenant_name": "Other Inc",
            "tenant_slug": "other-inc",
        },
    )
    other_token = other_signup.json()["data"]["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    cross_tenant = client.get(f"/api/v1/tasks/{task_id}", headers=other_headers)
    assert cross_tenant.status_code == 404


def test_audit_logs_on_login(client, auth_headers):
    logs = client.get("/api/v1/audit-logs", headers=auth_headers)
    assert logs.status_code == 200
    actions = {entry["action"] for entry in logs.json()["data"]}
    assert "login" in actions or "signup" in actions


def test_non_admin_cannot_approve_pipeline(client, db):
    from backend.auth.security import hash_password
    from backend.db_models.role import Role
    from backend.db_models.tenant import Tenant
    from backend.db_models.user import User
    from backend.services.auth_service import AuthService

    tenant = Tenant(name="RBAC Co", slug="rbac-co")
    db.add(tenant)
    db.flush()

    dev_role = db.query(Role).filter(Role.name == "developer").first()
    dev_user = User(
        tenant_id=tenant.id,
        role_id=dev_role.id,
        email="dev@rbac.com",
        password_hash=hash_password("password123"),
    )
    db.add(dev_user)
    db.commit()

    token = AuthService._build_token(dev_user)
    dev_headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/api/v1/tasks",
        json={"title": "RBAC Task", "description": "Task for RBAC approval testing with enough text."},
        headers=dev_headers,
    )
    task_id = create.json()["data"]["task_id"]
    client.post(f"/api/v1/tasks/{task_id}/run", headers=dev_headers)

    approval = client.post(
        f"/api/v1/tasks/{task_id}/approval",
        json={"approved": True},
        headers=dev_headers,
    )
    assert approval.status_code == 403
