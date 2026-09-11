import json

import pytest

from context.finding_repository import FindingRepository
from context.manager import ContextManager
from context.repository import ContextRepository
from utils.schemas import FindingAnalysis, SeverityClassification, ReportSection


def make_manager(tmp_path):
    project_repo = ContextRepository(tmp_path / "projects")
    finding_repo = FindingRepository(tmp_path / "findings")

    manager = ContextManager(
        repository=project_repo,
        finding_repository=finding_repo,
    )

    return manager


def create_project_and_finding(manager):
    manager.create_project(
        project_id="XPConnect",
        target="https://example.com",
        scope=["https://example.com/api"],
    )

    manager.create_finding(
        project_id="XPConnect",
        finding_id="VAPT-001",
        endpoint="/api/users",
        observation="User data exposed",
        evidence="HTTP 200 response",
        request_evidence="GET /api/users",
        affected_roles="Authenticated users",
    )


def test_successful_intelligence_generation(tmp_path, monkeypatch):
    manager = make_manager(tmp_path)
    create_project_and_finding(manager)

    captured = {}

    class DummyCrew:
        def __init__(self, *args, **kwargs):
            pass

        def kickoff(self, inputs=None):
            captured["inputs"] = inputs

    monkeypatch.setattr("context.manager.Crew", DummyCrew)

    def fake_parse(task, model):
        if model.__name__ == "FindingAnalysis":
            return FindingAnalysis(vulnerability_title="Test", technical_description="Details")
        if model.__name__ == "SeverityClassification":
            return SeverityClassification(severity="HIGH", cwe_ids=[], owasp_categories=[], wstg_categories=[], justification="evidence")
        return ReportSection(title="T", severity="HIGH", description="D", affected_endpoints=[], steps_to_reproduce=[], remediation=["Fix it"], remediation_recommendations=[], references=[])

    monkeypatch.setattr("context.manager.parse_task_output", fake_parse)

    updated = manager.generate_finding_intelligence("XPConnect", "VAPT-001")

    assert updated.ai_severity == "HIGH"
    assert updated.ai_remediation == ["Fix it"]
    assert updated.confirmed_severity is None
    assert updated.review_status == "unreviewed"
    # tester-provided fields remain unchanged
    assert updated.endpoint == "/api/users"


def test_project_context_is_supplied_to_ai(monkeypatch, tmp_path):
    manager = make_manager(tmp_path)
    create_project_and_finding(manager)

    captured = {}

    class DummyCrew:
        def __init__(self, *args, **kwargs):
            pass

        def kickoff(self, inputs=None):
            captured["inputs"] = inputs

    monkeypatch.setattr("context.manager.Crew", DummyCrew)

    def fake_parse(task, model):
        if model.__name__ == "FindingAnalysis":
            return FindingAnalysis()
        if model.__name__ == "SeverityClassification":
            return SeverityClassification(severity="LOW", cwe_ids=[], owasp_categories=[], wstg_categories=[], justification="")
        return ReportSection(title="T", severity="LOW", description="D", affected_endpoints=[], steps_to_reproduce=[], remediation=[], remediation_recommendations=[], references=[])

    monkeypatch.setattr("context.manager.parse_task_output", fake_parse)

    manager.generate_finding_intelligence("XPConnect", "VAPT-001")

    assert "project_context" in captured["inputs"]
    assert json.loads(captured["inputs"]["project_context"]) == manager.get_project("XPConnect").model_dump()


def test_missing_project_raises(tmp_path):
    manager = make_manager(tmp_path)

    with pytest.raises(FileNotFoundError):
        manager.generate_finding_intelligence("MISSING", "VAPT-001")


def test_missing_finding_raises(tmp_path):
    manager = make_manager(tmp_path)
    manager.create_project(project_id="P1", target="t")

    with pytest.raises(FileNotFoundError):
        manager.generate_finding_intelligence("P1", "NOPE")


def test_ai_generation_failure_does_not_corrupt(monkeypatch, tmp_path):
    manager = make_manager(tmp_path)
    create_project_and_finding(manager)

    class BrokenCrew:
        def __init__(self, *args, **kwargs):
            pass

        def kickoff(self, inputs=None):
            raise RuntimeError("AI backend failure")

    monkeypatch.setattr("context.manager.Crew", BrokenCrew)

    with pytest.raises(RuntimeError):
        manager.generate_finding_intelligence("XPConnect", "VAPT-001")

    # Ensure finding remains unchanged
    found = manager.get_finding("XPConnect", "VAPT-001")
    assert found.ai_analysis is None


def test_reviewer_confirmed_values_not_overwritten(monkeypatch, tmp_path):
    manager = make_manager(tmp_path)
    create_project_and_finding(manager)

    # Manually set confirmed values
    manager.update_finding("XPConnect", "VAPT-001", {
        "ai_severity": "HIGH",
        "ai_remediation": ["Old fix"],
        "confirmed_severity": "CRITICAL",
        "confirmed_remediation": ["Reviewer fix"],
        "review_status": "overridden",
    })

    captured = {}

    class DummyCrew:
        def __init__(self, *args, **kwargs):
            pass

        def kickoff(self, inputs=None):
            captured["inputs"] = inputs

    monkeypatch.setattr("context.manager.Crew", DummyCrew)

    def fake_parse(task, model):
        if model.__name__ == "FindingAnalysis":
            return FindingAnalysis(vulnerability_title="X")
        if model.__name__ == "SeverityClassification":
            return SeverityClassification(severity="LOW", cwe_ids=[], owasp_categories=[], wstg_categories=[], justification="")
        return ReportSection(title="T", severity="LOW", description="D", affected_endpoints=[], steps_to_reproduce=[], remediation=["New fix"], remediation_recommendations=[], references=[])

    monkeypatch.setattr("context.manager.parse_task_output", fake_parse)

    updated = manager.generate_finding_intelligence("XPConnect", "VAPT-001")

    # Confirmed values preserved and AI recommendations not overwritten
    assert updated.confirmed_severity == "CRITICAL"
    assert updated.confirmed_remediation == ["Reviewer fix"]
    assert updated.ai_severity == "HIGH"


def test_regenerate_ai_updates_when_no_confirmed(monkeypatch, tmp_path):
    manager = make_manager(tmp_path)
    create_project_and_finding(manager)

    class DummyCrew:
        def __init__(self, *args, **kwargs):
            pass

        def kickoff(self, inputs=None):
            pass

    monkeypatch.setattr("context.manager.Crew", DummyCrew)

    def fake_parse_first(task, model):
        if model.__name__ == "FindingAnalysis":
            return FindingAnalysis(vulnerability_title="First")
        if model.__name__ == "SeverityClassification":
            return SeverityClassification(severity="MEDIUM", cwe_ids=[], owasp_categories=[], wstg_categories=[], justification="")
        return ReportSection(title="T", severity="MEDIUM", description="D", affected_endpoints=[], steps_to_reproduce=[], remediation=["Fix A"], remediation_recommendations=[], references=[])

    monkeypatch.setattr("context.manager.parse_task_output", fake_parse_first)

    first = manager.generate_finding_intelligence("XPConnect", "VAPT-001")
    assert first.ai_severity == "MEDIUM"
    assert first.ai_remediation == ["Fix A"]

    def fake_parse_second(task, model):
        if model.__name__ == "FindingAnalysis":
            return FindingAnalysis(vulnerability_title="Second")
        if model.__name__ == "SeverityClassification":
            return SeverityClassification(severity="HIGH", cwe_ids=[], owasp_categories=[], wstg_categories=[], justification="")
        return ReportSection(title="T", severity="HIGH", description="D", affected_endpoints=[], steps_to_reproduce=[], remediation=["Fix B"], remediation_recommendations=[], references=[])

    monkeypatch.setattr("context.manager.parse_task_output", fake_parse_second)

    second = manager.generate_finding_intelligence("XPConnect", "VAPT-001")
    # AI recommendation updated
    assert second.ai_severity == "HIGH"
    assert second.ai_remediation == ["Fix B"]


def test_backward_compatibility_with_legacy_finding(tmp_path, monkeypatch):
    manager = make_manager(tmp_path)
    manager.create_project(project_id="LEG", target="t")

    # create a legacy payload without ai fields via direct repository write
    manager.create_finding(project_id="LEG", finding_id="V1", endpoint="/x", observation="obs", evidence="e")

    class DummyCrew:
        def __init__(self, *args, **kwargs):
            pass

        def kickoff(self, inputs=None):
            pass

    monkeypatch.setattr("context.manager.Crew", DummyCrew)

    def fake_parse(task, model):
        if model.__name__ == "FindingAnalysis":
            return FindingAnalysis(vulnerability_title="L")
        if model.__name__ == "SeverityClassification":
            return SeverityClassification(severity="LOW", cwe_ids=[], owasp_categories=[], wstg_categories=[], justification="")
        return ReportSection(title="T", severity="LOW", description="D", affected_endpoints=[], steps_to_reproduce=[], remediation=["Fix L"], remediation_recommendations=[], references=[])

    monkeypatch.setattr("context.manager.parse_task_output", fake_parse)

    updated = manager.generate_finding_intelligence("LEG", "V1")
    assert updated.ai_severity == "LOW"
    assert updated.ai_remediation == ["Fix L"]
