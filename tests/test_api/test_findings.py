from pathlib import Path

from fastapi.testclient import TestClient

import api_server
from context import ContextManager, ContextRepository, FindingRepository


def make_client(tmp_path: Path):
    repository = ContextRepository(
        str(tmp_path / "projects")
    )

    finding_repository = FindingRepository(
        str(tmp_path / "findings")
    )

    api_server.context_manager = ContextManager(
        repository=repository,
        finding_repository=finding_repository,
    )

    client = TestClient(api_server.app)

    client.post(
        "/projects",
        json={
            "project_id": "TEST-001",
            "target": "https://example.com",
        },
    )

    return client


def test_create_finding(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/projects/TEST-001/findings",
        json={
            "finding_id": "VAPT-001",
            "endpoint": "/api/users",
            "observation": "IDOR vulnerability",
            "evidence": "User A accessed User B data",
            "affected_roles": "Authenticated User",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["project_id"] == "TEST-001"
    assert data["finding_id"] == "VAPT-001"
    assert data["observation"] == "IDOR vulnerability"


def test_create_finding_requires_project(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/projects/DOES-NOT-EXIST/findings",
        json={
            "finding_id": "VAPT-001",
        },
    )

    assert response.status_code == 404


def test_duplicate_finding(tmp_path):
    client = make_client(tmp_path)

    payload = {
        "finding_id": "VAPT-001",
    }

    first = client.post(
        "/projects/TEST-001/findings",
        json=payload,
    )

    second = client.post(
        "/projects/TEST-001/findings",
        json=payload,
    )

    assert first.status_code == 200
    assert second.status_code == 409


def test_get_finding(tmp_path):
    client = make_client(tmp_path)

    client.post(
        "/projects/TEST-001/findings",
        json={
            "finding_id": "VAPT-001",
            "observation": "Test finding",
        },
    )

    response = client.get(
        "/projects/TEST-001/findings/VAPT-001",
    )

    assert response.status_code == 200
    assert response.json()["finding_id"] == "VAPT-001"


def test_get_missing_finding(tmp_path):
    client = make_client(tmp_path)

    response = client.get(
        "/projects/TEST-001/findings/VAPT-999",
    )

    assert response.status_code == 404


def test_list_findings(tmp_path):
    client = make_client(tmp_path)

    client.post(
        "/projects/TEST-001/findings",
        json={"finding_id": "VAPT-002"},
    )

    client.post(
        "/projects/TEST-001/findings",
        json={"finding_id": "VAPT-001"},
    )

    response = client.get(
        "/projects/TEST-001/findings",
    )

    assert response.status_code == 200
    assert response.json() == [
        "VAPT-001",
        "VAPT-002",
    ]


def test_update_finding(tmp_path):
    client = make_client(tmp_path)

    client.post(
        "/projects/TEST-001/findings",
        json={
            "finding_id": "VAPT-001",
            "observation": "Original",
        },
    )

    response = client.put(
        "/projects/TEST-001/findings/VAPT-001",
        json={
            "observation": "Updated",
            "status": "confirmed",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["observation"] == "Updated"
    assert data["status"] == "confirmed"
    assert data["version"] == 2


def test_delete_finding(tmp_path):
    client = make_client(tmp_path)

    client.post(
        "/projects/TEST-001/findings",
        json={"finding_id": "VAPT-001"},
    )

    response = client.delete(
        "/projects/TEST-001/findings/VAPT-001",
    )

    assert response.status_code == 200
    assert response.json()["deleted"] is True

    response = client.get(
        "/projects/TEST-001/findings/VAPT-001",
    )

    assert response.status_code == 404


def test_generate_project_finding_report_success(tmp_path, monkeypatch):
    client = make_client(tmp_path)

    client.post(
        "/projects/TEST-001",
        json={
            "project_id": "TEST-001",
            "target": "https://example.com",
            "scope": ["/api/*"],
            "technologies": ["FastAPI"],
            "authentication": {"type": "JWT"},
            "roles": ["admin", "user"],
        },
    )

    client.post(
        "/projects/TEST-001/findings",
        json={
            "finding_id": "VAPT-001",
            "endpoint": "/api/users",
            "observation": "User data returned without access checks.",
            "evidence": "HTTP 200 response with user records.",
            "request_evidence": "GET /api/users",
            "affected_roles": "Authenticated user",
        },
    )

    persisted = {
        "target": "https://example.com",
        "sections": [{
            "title": "Exposed user records",
            "severity": "HIGH",
            "owasp": "Broken Access Control (OWASP A01:2025)",
            "cwe": "CWE-639",
            "wstg": "Testing for Access Control (WSTG-ATHZ-03)",
            "description": "User data was exposed without access checks.",
            "business_impact": "Customer data exposure.",
            "affected_endpoints": [],
            "steps_to_reproduce": ["Call the endpoint as an authenticated user."],
            "proof_of_concept": "HTTP 200 response returned user records.",
            "remediation": ["Enforce authorization checks."],
            "references": ["OWASP ASVS"],
            "finding_id": "VAPT-001",
            "section_number": "5.1",
            "cvss_score": 7.5,
        }],
        "report_markdown": "# Test report",
    }

    monkeypatch.setattr(api_server, "generate_and_persist", lambda payload: persisted)

    response = client.post("/projects/TEST-001/findings/VAPT-001/generate")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Exposed user records"
    assert data["finding_id"] == "VAPT-001"
    assert data["severity"] == "HIGH"
    assert data["owasp"] == "Broken Access Control (OWASP A01:2025)"


def test_generate_project_finding_report_missing_project_returns_404(tmp_path, monkeypatch):
    client = make_client(tmp_path)
    monkeypatch.setattr(api_server, "generate_and_persist", lambda payload: {"sections": []})

    response = client.post("/projects/DOES-NOT-EXIST/findings/VAPT-001/generate")

    assert response.status_code == 404


def test_generate_project_finding_report_missing_finding_returns_404(tmp_path, monkeypatch):
    client = make_client(tmp_path)
    client.post(
        "/projects/TEST-001",
        json={"project_id": "TEST-001", "target": "https://example.com"},
    )
    monkeypatch.setattr(api_server, "generate_and_persist", lambda payload: {"sections": []})

    response = client.post("/projects/TEST-001/findings/VAPT-999/generate")

    assert response.status_code == 404


def test_generate_project_finding_report_rejects_wrong_project_context(tmp_path, monkeypatch):
    client = make_client(tmp_path)

    client.post(
        "/projects/PROJECT-A",
        json={"project_id": "PROJECT-A", "target": "https://a.example.com"},
    )
    client.post(
        "/projects/PROJECT-B",
        json={"project_id": "PROJECT-B", "target": "https://b.example.com"},
    )
    client.post(
        "/projects/PROJECT-A/findings",
        json={"finding_id": "VAPT-001", "observation": "Sensitive data is exposed"},
    )
    monkeypatch.setattr(api_server, "generate_and_persist", lambda payload: {"sections": []})

    response = client.post("/projects/PROJECT-B/findings/VAPT-001/generate")

    assert response.status_code == 404


def test_legacy_report_generation_endpoints_remain_compatible(tmp_path, monkeypatch):
    client = make_client(tmp_path)

    persisted = {
        "target": "https://example.com",
        "sections": [{
            "title": "Legacy report",
            "severity": "MEDIUM",
            "owasp": "Broken Access Control",
            "cwe": "CWE-200",
            "wstg": "N/A",
            "description": "Legacy test description.",
            "business_impact": "Reduced assurance.",
            "affected_endpoints": [],
            "steps_to_reproduce": ["1. Trigger the endpoint."],
            "proof_of_concept": "Observed response.",
            "remediation": ["Validate access."],
            "references": [],
            "finding_id": "VAPT-001",
            "section_number": "5.1",            
        }],
        "report_markdown": "# Legacy",
    }

    monkeypatch.setattr(api_server, "generate_and_persist", lambda payload: persisted)

    report_response = client.post(
        "/generate-report",
        json={
            "target": "https://example.com",
            "finding": {
                "endpoint": "/api/users",
                "observation": "Data exposure",
                "evidence": "HTTP 200",
            },
        },
    )
    assert report_response.status_code == 200
    assert report_response.json()["title"] == "Legacy report"

    full_response = client.post(
        "/generate",
        json={
            "target": "https://example.com",
            "findings": [{
                "endpoint": "/api/users",
                "observation": "Data exposure",
                "evidence": "HTTP 200",
            }],
        },
    )
    assert full_response.status_code == 200
    assert full_response.json()["title"] == "Legacy report"
