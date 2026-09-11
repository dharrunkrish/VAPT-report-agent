from pathlib import Path

from fastapi.testclient import TestClient

import api_server
from context import ContextManager, ContextRepository, FindingRepository


def make_client(tmp_path: Path):
    repository = ContextRepository(str(tmp_path / "projects"))
    finding_repository = FindingRepository(str(tmp_path / "findings"))

    api_server.context_manager = ContextManager(
        repository=repository,
        finding_repository=finding_repository,
    )

    client = TestClient(api_server.app)

    client.post(
        "/projects",
        json={"project_id": "PRJ", "target": "https://example.com"},
    )

    client.post(
        "/projects/PRJ/findings",
        json={"finding_id": "F1", "endpoint": "/x", "observation": "o", "evidence": "e"},
    )

    return client


def test_severity_approval(tmp_path: Path):
    client = make_client(tmp_path)
    # seed AI recommendation via manager
    api_server.context_manager.update_finding("PRJ", "F1", {"ai_severity": "HIGH"})

    resp = client.patch("/projects/PRJ/findings/F1/review", json={"severity_action": "approve"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_severity"] == "HIGH"
    assert data["confirmed_severity"] == "HIGH"


def test_severity_override(tmp_path: Path):
    client = make_client(tmp_path)
    api_server.context_manager.update_finding("PRJ", "F1", {"ai_severity": "HIGH"})

    resp = client.patch("/projects/PRJ/findings/F1/review", json={"severity_action": "override", "severity": "MEDIUM"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_severity"] == "HIGH"
    assert data["confirmed_severity"] == "MEDIUM"


def test_remediation_approval(tmp_path: Path):
    client = make_client(tmp_path)
    api_server.context_manager.update_finding("PRJ", "F1", {"ai_remediation": ["AI fix"]})

    resp = client.patch("/projects/PRJ/findings/F1/review", json={"remediation_action": "approve"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_remediation"] == ["AI fix"]
    assert data["confirmed_remediation"] == ["AI fix"]


def test_remediation_override(tmp_path: Path):
    client = make_client(tmp_path)
    api_server.context_manager.update_finding("PRJ", "F1", {"ai_remediation": ["AI fix"]})

    resp = client.patch("/projects/PRJ/findings/F1/review", json={"remediation_action": "override", "remediation": ["Reviewer fix"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_remediation"] == ["AI fix"]
    assert data["confirmed_remediation"] == ["Reviewer fix"]


def test_partial_and_complete_review(tmp_path: Path):
    client = make_client(tmp_path)
    api_server.context_manager.update_finding("PRJ", "F1", {"ai_severity": "LOW", "ai_remediation": ["AI fix"]})

    # Partial: severity only
    resp1 = client.patch("/projects/PRJ/findings/F1/review", json={"severity_action": "approve"})
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["confirmed_severity"] == "LOW"

    # Complete: approve remediation as well
    resp2 = client.patch("/projects/PRJ/findings/F1/review", json={"remediation_action": "approve"})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["confirmed_remediation"] == ["AI fix"]
    # When both confirmed and match AI, review_status should be approved
    assert data2["review_status"] in ("approved", "reviewed")


def test_missing_project_or_finding(tmp_path: Path):
    client = make_client(tmp_path)

    resp = client.patch("/projects/NOPE/findings/F1/review", json={"severity_action": "approve"})
    assert resp.status_code == 404

    resp2 = client.patch("/projects/PRJ/findings/NOPE/review", json={"severity_action": "approve"})
    assert resp2.status_code == 404


def test_finding_belongs_to_another_project(tmp_path: Path):
    client = make_client(tmp_path)
    # create another project and a finding there
    client.post("/projects", json={"project_id": "OTHER", "target": "t"})
    client.post("/projects/OTHER/findings", json={"finding_id": "X1"})

    # Attempt to review OTHER/X1 via PRJ path should 404
    resp = client.patch("/projects/PRJ/findings/X1/review", json={"severity_action": "approve"})
    assert resp.status_code == 404


def test_invalid_severity_and_actions_and_empty_remediation(tmp_path: Path):
    client = make_client(tmp_path)
    api_server.context_manager.update_finding("PRJ", "F1", {"ai_severity": "HIGH", "ai_remediation": ["AI"]})

    # invalid severity value -> 400
    resp = client.patch("/projects/PRJ/findings/F1/review", json={"severity_action": "override", "severity": "BAD"})
    assert resp.status_code == 400

    # invalid action -> 400
    resp2 = client.patch("/projects/PRJ/findings/F1/review", json={"severity_action": "invalid_action"})
    assert resp2.status_code == 400

    # empty remediation -> 400
    resp3 = client.patch("/projects/PRJ/findings/F1/review", json={"remediation_action": "override", "remediation": []})
    assert resp3.status_code == 400


def test_response_contains_projectfinding_and_preserves_ai_fields(tmp_path: Path):
    client = make_client(tmp_path)
    api_server.context_manager.update_finding("PRJ", "F1", {"ai_severity": "HIGH", "ai_remediation": ["A"]})

    resp = client.patch("/projects/PRJ/findings/F1/review", json={"severity_action": "approve", "remediation_action": "approve"})
    assert resp.status_code == 200
    data = resp.json()
    # response contains ProjectFinding fields
    assert data["finding_id"] == "F1"
    assert data["project_id"] == "PRJ"
    # AI fields preserved
    assert data["ai_severity"] == "HIGH"
    assert data["ai_remediation"] == ["A"]
    # confirmed values present
    assert data["confirmed_severity"] == "HIGH"
    assert data["confirmed_remediation"] == ["A"]


def test_invalid_payload_types_return_422(tmp_path: Path):
    """Send payloads with wrong types to trigger FastAPI/Pydantic 422 validation."""
    client = make_client(tmp_path)

    # severity_action should be a string; sending an int should 422
    resp = client.patch("/projects/PRJ/findings/F1/review", json={"severity_action": 123})
    assert resp.status_code == 422

    # remediation should be a list of strings; sending a string should 422
    resp2 = client.patch("/projects/PRJ/findings/F1/review", json={"remediation_action": "override", "remediation": "not-a-list"})
    assert resp2.status_code == 422


def test_effective_severity_and_remediation_used_in_report_generation_confirmed_precedence(tmp_path: Path, monkeypatch):
    client = make_client(tmp_path)

    # Seed AI values then apply reviewer overrides (to satisfy model validators)
    api_server.context_manager.update_finding("PRJ", "F1", {"ai_severity": "HIGH", "ai_remediation": ["AI fix"]})
    # Use the review endpoint to set confirmed values (override)
    r = client.patch("/projects/PRJ/findings/F1/review", json={"severity_action": "override", "severity": "LOW", "remediation_action": "override", "remediation": ["Reviewer fix"]})
    assert r.status_code == 200

    captured = {}

    def fake_generate_and_persist(payload):
        captured["payload"] = payload
        return {
            "sections": [{
                "title": "T",
                "severity": "LOW",
                "description": "d",
                "remediation": ["r"],
                "affected_endpoints": [],
                "finding_id": "F1",
            }],
            "report_markdown": "#",
        }

    monkeypatch.setattr(api_server, "generate_and_persist", fake_generate_and_persist)

    resp = client.post("/projects/PRJ/findings/F1/generate")
    assert resp.status_code == 200
    assert captured["payload"]["finding"]["severity"] == "LOW"
    assert captured["payload"]["finding"]["remediation"] == ["Reviewer fix"]


def test_effective_severity_and_remediation_used_in_report_generation_ai_fallback(tmp_path: Path, monkeypatch):
    client = make_client(tmp_path)

    # Seed only AI values (AI should be used when confirmed missing)
    api_server.context_manager.update_finding("PRJ", "F1", {"ai_severity": "MEDIUM", "ai_remediation": ["AI only fix"]})
    # Ensure no confirmed values exist
    f = api_server.context_manager.get_finding("PRJ", "F1")
    assert f.confirmed_severity is None
    assert not f.confirmed_remediation

    captured = {}

    def fake_generate_and_persist(payload):
        captured["payload"] = payload
        return {
            "sections": [{
                "title": "T",
                "severity": "MEDIUM",
                "description": "d",
                "remediation": ["r"],
                "affected_endpoints": [],
                "finding_id": "F1",
            }],
            "report_markdown": "#",
        }

    monkeypatch.setattr(api_server, "generate_and_persist", fake_generate_and_persist)

    resp = client.post("/projects/PRJ/findings/F1/generate")
    assert resp.status_code == 200
    assert captured["payload"]["finding"]["severity"] == "MEDIUM"
    assert captured["payload"]["finding"]["remediation"] == ["AI only fix"]


def test_legacy_finding_behavior_unchanged_in_report_generation(tmp_path: Path, monkeypatch):
    client = make_client(tmp_path)

    # Legacy finding without AI/reviewer fields
    # ensure generate still proceeds and the finding payload does not supply reviewed fields
    captured = {}

    def fake_generate_and_persist(payload):
        captured["payload"] = payload
        return {
            "sections": [{
                "title": "T",
                "severity": "N/A",
                "description": "d",
                "remediation": [],
                "affected_endpoints": [],
                "finding_id": "F1",
            }],
            "report_markdown": "#",
        }

    monkeypatch.setattr(api_server, "generate_and_persist", fake_generate_and_persist)

    resp = client.post("/projects/PRJ/findings/F1/generate")
    assert resp.status_code == 200
    # Legacy finding should not have severity/remediation keys set
    assert "severity" not in captured["payload"]["finding"] or captured["payload"]["finding"]["severity"] in (None, "")
    assert "remediation" not in captured["payload"]["finding"] or captured["payload"]["finding"]["remediation"] in (None, [], "")
