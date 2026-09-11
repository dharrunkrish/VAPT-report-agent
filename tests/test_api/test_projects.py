from fastapi.testclient import TestClient

import api_server
from context.repository import ContextRepository
from context.manager import ContextManager


def make_client(tmp_path):
    repository = ContextRepository(str(tmp_path))
    api_server.context_manager = ContextManager(repository)

    return TestClient(api_server.app)


def test_create_project(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/projects",
        json={
            "project_id": "TEST-001",
            "target": "https://example.com",
            "scope": ["/api/*"],
            "technologies": ["REST API"],
            "roles": ["User"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["project_id"] == "TEST-001"
    assert data["target"] == "https://example.com"
    assert data["scope"] == ["/api/*"]


def test_get_project(tmp_path):
    client = make_client(tmp_path)

    create_response = client.post(
        "/projects",
        json={
            "project_id": "TEST-002",
            "target": "https://example.com",
        },
    )

    assert create_response.status_code == 200

    response = client.get("/projects/TEST-002")

    assert response.status_code == 200
    assert response.json()["project_id"] == "TEST-002"


def test_get_missing_project(tmp_path):
    client = make_client(tmp_path)

    response = client.get("/projects/DOES-NOT-EXIST")

    assert response.status_code == 404


def test_duplicate_project(tmp_path):
    client = make_client(tmp_path)

    payload = {
        "project_id": "TEST-003",
        "target": "https://example.com",
    }

    first = client.post("/projects", json=payload)
    second = client.post("/projects", json=payload)

    assert first.status_code == 200
    assert second.status_code == 409


def test_create_project_empty_project_id(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/projects",
        json={
            "project_id": "",
            "target": "https://example.com",
        },
    )

    assert response.status_code == 400


def test_create_project_empty_target(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/projects",
        json={
            "project_id": "TEST-004",
            "target": "",
        },
    )

    assert response.status_code == 400