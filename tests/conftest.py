from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-unit-tests-only"
os.environ["UPLOAD_DIR"] = "test_uploads"

from backend.config import get_settings

get_settings.cache_clear()

from backend.database.session import SessionLocal, get_db, init_db
from backend.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> Generator[None, None, None]:
    init_db()
    yield


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    import uuid

    suffix = uuid.uuid4().hex[:8]
    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"admin-{suffix}@example.com",
            "password": "securepass123",
            "full_name": "Test Admin",
            "tenant_name": f"Acme Corp {suffix}",
            "tenant_slug": f"acme-{suffix}",
        },
    )
    assert signup.status_code == 200, signup.text
    token = signup.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
