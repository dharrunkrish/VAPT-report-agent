import pytest

from context.finding_repository import FindingRepository
from context.manager import ContextManager
from context.repository import ContextRepository


def make_manager(tmp_path):
    project_repo = ContextRepository(tmp_path / "projects")
    finding_repo = FindingRepository(tmp_path / "findings")

    manager = ContextManager(
        repository=project_repo,
        finding_repository=finding_repo,
    )

    return manager


def create_project_and_finding(manager):
    manager.create_project(project_id="P1", target="t")

    manager.create_finding(
        project_id="P1",
        finding_id="F1",
        endpoint="/x",
        observation="o",
        evidence="e",
    )


def test_approve_ai_severity(tmp_path):
    manager = make_manager(tmp_path)
    create_project_and_finding(manager)

    # seed AI recommendation
    manager.update_finding("P1", "F1", {"ai_severity": "HIGH", "ai_remediation": ["AI fix"]})

    updated = manager.review_finding("P1", "F1", severity_action="approve")

    assert updated.ai_severity == "HIGH"
    assert updated.confirmed_severity == "HIGH"
    assert updated.review_status in ("reviewed", "approved")


def test_override_severity(tmp_path):
    manager = make_manager(tmp_path)
    create_project_and_finding(manager)
    manager.update_finding("P1", "F1", {"ai_severity": "HIGH"})

    updated = manager.review_finding("P1", "F1", severity_action="override", severity="MEDIUM")

    assert updated.ai_severity == "HIGH"
    assert updated.confirmed_severity == "MEDIUM"
    assert updated.review_status == "overridden"


def test_approve_ai_remediation(tmp_path):
    manager = make_manager(tmp_path)
    create_project_and_finding(manager)

    manager.update_finding("P1", "F1", {"ai_remediation": ["AI fix"]})

    updated = manager.review_finding("P1", "F1", remediation_action="approve")

    assert updated.ai_remediation == ["AI fix"]
    assert updated.confirmed_remediation == ["AI fix"]


def test_override_remediation(tmp_path):
    manager = make_manager(tmp_path)
    create_project_and_finding(manager)
    manager.update_finding("P1", "F1", {"ai_remediation": ["AI fix"]})

    updated = manager.review_finding("P1", "F1", remediation_action="override", remediation=["Reviewer fix"]) 

    assert updated.ai_remediation == ["AI fix"]
    assert updated.confirmed_remediation == ["Reviewer fix"]
    assert updated.review_status == "overridden"


def test_partial_review_severity_only(tmp_path):
    manager = make_manager(tmp_path)
    create_project_and_finding(manager)
    manager.update_finding("P1", "F1", {"ai_severity": "LOW"})

    updated = manager.review_finding("P1", "F1", severity_action="approve")
    assert updated.confirmed_severity == "LOW"
    assert updated.confirmed_remediation == []
    assert updated.review_status == "reviewed"


def test_invalid_severity_rejected(tmp_path):
    manager = make_manager(tmp_path)
    create_project_and_finding(manager)

    with pytest.raises(ValueError):
        manager.review_finding("P1", "F1", severity_action="override", severity="INVALID")


def test_empty_remediation_rejected(tmp_path):
    manager = make_manager(tmp_path)
    create_project_and_finding(manager)

    with pytest.raises(ValueError):
        manager.review_finding("P1", "F1", remediation_action="override", remediation=[])


def test_missing_project_or_finding(tmp_path):
    manager = make_manager(tmp_path)

    with pytest.raises(FileNotFoundError):
        manager.review_finding("NO", "F1", severity_action="approve")

    manager.create_project(project_id="P2", target="t")
    with pytest.raises(FileNotFoundError):
        manager.review_finding("P2", "NOPE", severity_action="approve")


def test_reviewer_confirmed_survives_regeneration(tmp_path, monkeypatch):
    # Ensure confirmed values survive subsequent AI regeneration
    manager = make_manager(tmp_path)
    manager.create_project(project_id="PR", target="t")
    manager.create_finding(project_id="PR", finding_id="G1", endpoint="/x", observation="o", evidence="e")

    # seed initial AI recommendation and reviewer override
    manager.update_finding("PR", "G1", {"ai_severity": "HIGH", "ai_remediation": ["AI v1"]})
    manager.review_finding("PR", "G1", severity_action="override", severity="MEDIUM")

    # Simulate regeneration that updates ai fields
    manager.update_finding("PR", "G1", {"ai_severity": "CRITICAL", "ai_remediation": ["AI v2"]})

    found = manager.get_finding("PR", "G1")
    assert found.ai_severity == "CRITICAL"
    # confirmed remains the reviewer value
    assert found.confirmed_severity == "MEDIUM"
