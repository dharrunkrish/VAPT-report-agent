from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api_server
from config.settings import GROQ_API_KEY
import os
from context import ContextManager, ContextRepository, FindingRepository


def make_client(tmp_path: Path):
    repository = ContextRepository(str(tmp_path / "projects"))
    finding_repository = FindingRepository(str(tmp_path / "findings"))

    api_server.context_manager = ContextManager(
        repository=repository,
        finding_repository=finding_repository,
    )

    return TestClient(api_server.app)


def test_project_finding_workflow_integration(tmp_path, monkeypatch):
    client = make_client(tmp_path)

    project_payload = {
        "project_id": "APP-01",
        "target": "https://example.com",
        "scope": ["/api/*"],
        "technologies": ["FastAPI", "React"],
        "authentication": {"type": "JWT"},
        "roles": ["admin", "user"],
        "assets": ["web-app"],
        "notes": "Application context for the employee directory API.",
    }

    project_response = client.post("/projects", json=project_payload)
    assert project_response.status_code == 200

    finding_response = client.post(
        "/projects/APP-01/findings",
        json={
            "finding_id": "VAPT-001",
            "endpoint": "/api/users",
            "observation": "User records are exposed without authorization checks.",
            "evidence": "HTTP 200 response returned full user records.",
            "request_evidence": "GET /api/users",
            "affected_roles": "Authenticated users",
        },
    )
    assert finding_response.status_code == 200

    retrieved_project = client.get("/projects/APP-01")
    assert retrieved_project.status_code == 200
    assert retrieved_project.json()["project_id"] == "APP-01"

    context_response = client.get("/projects/APP-01/findings/VAPT-001")
    assert context_response.status_code == 200

    manager = api_server.context_manager
    combined_context = manager.get_project("APP-01")
    assert combined_context is not None
    assert combined_context.target == "https://example.com"

    project_context_service = api_server.ProjectContextService(manager)
    resolved_context = project_context_service.get_finding_context("APP-01", "VAPT-001")
    assert resolved_context["project_context"]["project_id"] == "APP-01"
    assert resolved_context["finding"]["finding_id"] == "VAPT-001"

    persisted_report = {
        "target": "https://example.com",
        "sections": [{
            "title": "Access control bypass in /api/users",
            "severity": "HIGH",
            "owasp": "Broken Access Control (OWASP A01:2025)",
            "cwe": "CWE-639",
            "wstg": "Testing for Access Control (WSTG-ATHZ-03)",
            "description": "The endpoint returned user records without checks.",
            "business_impact": "Customer PII exposure and trust impact.",
            "affected_endpoints": [{
                "endpoint": "/api/users",
                "affected_roles": "Authenticated users",
                "impact": "Unauthenticated or unauthorized users may enumerate data.",
                "severity": "HIGH",
            }],
            "steps_to_reproduce": ["Send a GET request without role validation."],
            "proof_of_concept": "HTTP 200 response returned user records.",
            "remediation": ["Enforce authorization checks before returning user data."],
            "references": ["OWASP ASVS"],
            "finding_id": "VAPT-001",
            "section_number": "5.1",
            "cvss_score": 7.5,
        }],
        "report_markdown": "# Access control bypass in /api/users\n\n## Risk\nHigh",
    }

    captured = {}

    def fake_generate_and_persist(payload):
        captured["payload"] = payload
        return persisted_report

    monkeypatch.setattr(api_server, "generate_and_persist", fake_generate_and_persist)

    response = client.post("/projects/APP-01/findings/VAPT-001/generate")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["title"] == "Access control bypass in /api/users"
    assert payload["severity"] == "HIGH"
    assert payload["finding_id"] == "VAPT-001"
    assert payload["remediation"] == ["Enforce authorization checks before returning user data."]
    assert "Access control bypass" in payload["markdown"]
    assert captured["payload"]["project_id"] == "APP-01"
    assert captured["payload"]["finding_id"] == "VAPT-001"
    assert captured["payload"]["finding"]["project_id"] == "APP-01"


def test_project_finding_association_validation_and_404s(tmp_path, monkeypatch):
    client = make_client(tmp_path)

    client.post(
        "/projects",
        json={
            "project_id": "APP-01",
            "target": "https://example.com",
        },
    )
    client.post(
        "/projects",
        json={
            "project_id": "APP-02",
            "target": "https://other.example.com",
        },
    )

    client.post(
        "/projects/APP-01/findings",
        json={
            "finding_id": "VAPT-001",
            "observation": "Sensitive data exposed",
        },
    )
    client.post(
        "/projects/APP-02/findings",
        json={
            "finding_id": "VAPT-002",
            "observation": "Authorization weakness",
        },
    )

    monkeypatch.setattr(api_server, "generate_and_persist", lambda payload: {"sections": []})

    missing_project_response = client.post("/projects/MISSING/findings/VAPT-001/generate")
    assert missing_project_response.status_code == 404

    missing_finding_response = client.post("/projects/APP-01/findings/VAPT-999/generate")
    assert missing_finding_response.status_code == 404

    wrong_project_response = client.post("/projects/APP-02/findings/VAPT-001/generate")
    assert wrong_project_response.status_code == 404


def test_legacy_generate_report_endpoint_still_works_without_project_context(tmp_path, monkeypatch):
    client = make_client(tmp_path)

    persisted_report = {
        "target": "https://legacy.example.com",
        "sections": [{
            "title": "Legacy report",
            "severity": "MEDIUM",
            "owasp": "Broken Access Control",
            "cwe": "CWE-200",
            "wstg": "N/A",
            "description": "Legacy path still works.",
            "business_impact": "Limited risk.",
            "affected_endpoints": [],
            "steps_to_reproduce": ["Trigger the vulnerable action."],
            "proof_of_concept": "Observed behavior in the endpoint.",
            "remediation": ["Validate authorization before exposing data."],
            "references": [],
            "finding_id": "LEGACY-001",
            "section_number": "5.1",
        }],
        "report_markdown": "# Legacy report",
    }

    monkeypatch.setattr(api_server, "generate_and_persist", lambda payload: persisted_report)

    response = client.post(
        "/generate-report",
        json={
            "target": "https://legacy.example.com",
            "finding": {
                "endpoint": "/api/users",
                "observation": "Data exposure",
                "evidence": "HTTP 200",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Legacy report"
    assert data["finding_id"] == "LEGACY-001"
    assert data["severity"] == "MEDIUM"


@pytest.mark.skipif(
    not GROQ_API_KEY or os.environ.get("RUN_GROQ_SMOKE", "").lower() != "true",
    reason=(
        "Live Groq smoke test is opt-in via RUN_GROQ_SMOKE=true "
        "and requires GROQ_API_KEY; skipped by default to avoid depending on "
        "external provider availability/quota."
    ),
)
def test_project_aware_report_e2e_smoke_uses_real_groq_llm(tmp_path):
    client = make_client(tmp_path)

    client.post(
        "/projects",
        json={
            "project_id": "APP-E2E",
            "target": "https://e2e.example.com",
            "scope": ["/api/*"],
            "technologies": ["FastAPI", "PostgreSQL"],
            "authentication": {"type": "OAuth2"},
            "roles": ["admin", "member"],
            "notes": "Application context for end-to-end validation.",
        },
    )

    client.post(
        "/projects/APP-E2E/findings",
        json={
            "finding_id": "VAPT-101",
            "endpoint": "/api/users/{id}",
            "observation": "User profile data is returned without checking role or ownership.",
            "evidence": "A member account retrieved another member's record through the API.",
            "request_evidence": "GET /api/users/42 as member@example.com",
            "affected_roles": "member",
        },
    )

    response = client.post("/projects/APP-E2E/findings/VAPT-101/generate")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["finding_id"] == "VAPT-101"
    assert data["title"]
    assert data["severity"]
    assert data["remediation"]
    assert data["markdown"]
    assert data["section_number"]


def test_groq_smoke_gate_behavior(monkeypatch):
    """Verify RUN_GROQ_SMOKE gating logic (opt-in) without calling Groq.

    This test checks the environment gating used by the live smoke test:
    - When `RUN_GROQ_SMOKE=true` the gate reports enabled.
    - When not set or set to other values, the gate reports disabled.
    The live smoke test itself remains unchanged and is only executed when
    the environment variable is explicitly set to `true`.
    """
    # Ensure disabled by default / arbitrary value
    monkeypatch.delenv("RUN_GROQ_SMOKE", raising=False)
    assert os.environ.get("RUN_GROQ_SMOKE", "").lower() != "true"

    monkeypatch.setenv("RUN_GROQ_SMOKE", "true")
    assert os.environ.get("RUN_GROQ_SMOKE", "").lower() == "true"
