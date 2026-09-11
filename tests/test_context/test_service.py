import json

import pytest

from context.finding_repository import FindingRepository
from context.manager import ContextManager
from context.repository import ContextRepository
from context.service import ProjectContextService
from tasks.finding_analysis_task import JSON_SCHEMA_HINT, make_finding_analysis_task
from tasks.report_writer_task import make_report_writer_task
from tasks.severity_classification_task import make_severity_classification_task
from utils.schemas import FindingAnalysis, ReportSection, SeverityClassification


def make_service(tmp_path):
    project_repo = ContextRepository(tmp_path / "projects")
    finding_repo = FindingRepository(tmp_path / "findings")

    manager = ContextManager(
        repository=project_repo,
        finding_repository=finding_repo,
    )

    return manager, ProjectContextService(manager)


def create_project_and_finding(manager):
    manager.create_project(
        project_id="XPConnect",
        target="https://example.com",
        scope=["https://example.com/api"],
        technologies=["React", "FastAPI"],
        authentication={"type": "JWT"},
        roles=["admin", "user"],
        assets=["web-app"],
        notes="Test project",
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


def test_retrieves_project_and_finding(tmp_path):
    manager, service = make_service(tmp_path)
    create_project_and_finding(manager)

    result = service.get_finding_context(
        "XPConnect",
        "VAPT-001",
    )

    assert result["project_context"]["project_id"] == "XPConnect"
    assert result["project_context"]["target"] == "https://example.com"

    assert result["finding"]["finding_id"] == "VAPT-001"
    assert result["finding"]["endpoint"] == "/api/users"


def test_returns_expected_structure(tmp_path):
    manager, service = make_service(tmp_path)
    create_project_and_finding(manager)

    result = service.get_finding_context(
        "XPConnect",
        "VAPT-001",
    )

    assert set(result.keys()) == {
        "project_context",
        "finding",
    }

    assert isinstance(result["project_context"], dict)
    assert isinstance(result["finding"], dict)


def test_missing_project_raises_file_not_found(tmp_path):
    _, service = make_service(tmp_path)

    with pytest.raises(FileNotFoundError, match="Project 'missing' not found"):
        service.get_finding_context(
            "missing",
            "VAPT-001",
        )


def test_missing_finding_raises_file_not_found(tmp_path):
    manager, service = make_service(tmp_path)

    manager.create_project(
        project_id="XPConnect",
        target="https://example.com",
    )

    with pytest.raises(
        FileNotFoundError,
        match="Finding 'VAPT-999' not found",
    ):
        service.get_finding_context(
            "XPConnect",
            "VAPT-999",
        )


def test_context_is_json_serializable(tmp_path):
    manager, service = make_service(tmp_path)
    create_project_and_finding(manager)

    result = service.get_finding_context(
        "XPConnect",
        "VAPT-001",
    )

    serialized = json.dumps(result)

    assert isinstance(serialized, str)
    assert "XPConnect" in serialized
    assert "VAPT-001" in serialized


def test_generate_vapt_report_includes_context_for_context_aware_path(tmp_path, monkeypatch):
    manager, service = make_service(tmp_path)
    create_project_and_finding(manager)

    captured = {}

    def fake_process_single_finding(
        target,
        finding,
        llm,
        *,
        index,
        section_prefix,
        project_context=None,
    ):
        captured["project_context"] = project_context
        return ReportSection(
            title="Contextualized finding",
            severity="high",
            description="Context-aware path",
            target=target,
            finding_id="VAPT-001",
            section_number="5.1",
            affected_endpoints=[],
            steps_to_reproduce=[],
            remediation=[],
            remediation_recommendations=[],
            references=[],
        )

    monkeypatch.setattr("crew_orchestrator.get_llm", lambda **kwargs: object())
    monkeypatch.setattr("crew_orchestrator.process_single_finding", fake_process_single_finding)
    monkeypatch.setattr("crew_orchestrator._project_context_service", service)

    report = service.get_finding_context("XPConnect", "VAPT-001")
    payload = {
        "target": "https://example.com",
        "project_id": "XPConnect",
        "finding_id": "VAPT-001",
        "finding": {
            "endpoint": "/api/users",
            "observation": "User data exposed",
            "evidence": "HTTP 200 response",
        },
    }

    generate_vapt_report = __import__("crew_orchestrator", fromlist=["generate_vapt_report"]).generate_vapt_report
    generate_vapt_report(payload)

    assert captured["project_context"] is not None
    assert '"project_id": "XPConnect"' in captured["project_context"]
    assert '"target": "https://example.com"' in captured["project_context"]
    assert report["project_context"]["project_id"] == "XPConnect"


def test_generate_vapt_report_legacy_payload_is_still_compatible(monkeypatch):
    captured = {}

    def fake_process_single_finding(
        target,
        finding,
        llm,
        *,
        index,
        section_prefix,
        project_context=None,
    ):
        captured["project_context"] = project_context
        return ReportSection(
            title="Legacy finding",
            severity="medium",
            description="Legacy path",
            target=target,
            finding_id="VAPT-001",
            section_number="5.1",
            affected_endpoints=[],
            steps_to_reproduce=[],
            remediation=[],
            remediation_recommendations=[],
            references=[],
        )

    monkeypatch.setattr("crew_orchestrator.get_llm", lambda **kwargs: object())
    monkeypatch.setattr("crew_orchestrator.process_single_finding", fake_process_single_finding)

    generate_vapt_report = __import__("crew_orchestrator", fromlist=["generate_vapt_report"]).generate_vapt_report
    result = generate_vapt_report({
        "target": "https://example.com",
        "finding": {
            "endpoint": "/api/users",
            "observation": "User data exposed",
            "evidence": "HTTP 200 response",
        },
    })

    assert result["target"] == "https://example.com"
    assert result["findings_count"] == 1
    assert captured["project_context"] is None


def test_generate_vapt_report_frontend_style_payload_without_project_context(monkeypatch):
    captured = {}

    def fake_process_single_finding(
        target,
        finding,
        llm,
        *,
        index,
        section_prefix,
        project_context=None,
    ):
        captured["project_context"] = project_context
        return ReportSection(
            title="Frontend legacy finding",
            severity="medium",
            description="Legacy frontend payload",
            target=target,
            finding_id="VAPT-001",
            section_number="5.1",
            affected_endpoints=[],
            steps_to_reproduce=[],
            remediation=[],
            remediation_recommendations=[],
            references=[],
        )

    monkeypatch.setattr("crew_orchestrator.get_llm", lambda **kwargs: object())
    monkeypatch.setattr("crew_orchestrator.process_single_finding", fake_process_single_finding)

    generate_vapt_report = __import__("crew_orchestrator", fromlist=["generate_vapt_report"]).generate_vapt_report
    result = generate_vapt_report({
        "target": "https://staging-corp.com",
        "findings": [{
            "endpoint": "GET /api/v2/users/{id}",
            "observation": "test observation",
            "evidence": "test evidence",
        }],
    })

    assert result["target"] == "https://staging-corp.com"
    assert result["findings_count"] == 1
    assert captured["project_context"] is None


def test_process_single_finding_uses_empty_project_context_for_legacy_path(monkeypatch):
    captured = {}

    def fake_kickoff(crew, inputs):
        captured["inputs"] = inputs

    monkeypatch.setattr("crew_orchestrator._kickoff_crew", fake_kickoff)
    monkeypatch.setattr("crew_orchestrator.make_finding_analysis_agent", lambda llm=None: object())
    monkeypatch.setattr("crew_orchestrator.make_severity_agent", lambda llm=None: object())
    monkeypatch.setattr("crew_orchestrator.make_report_writer_agent", lambda llm=None: object())

    class DummyTask:
        def __init__(self):
            self.output = type("Output", (), {"pydantic": None, "json_dict": None, "raw": json.dumps({})})()
            self.context = None

    monkeypatch.setattr("crew_orchestrator.make_finding_analysis_task", lambda agent: DummyTask())
    monkeypatch.setattr("crew_orchestrator.make_severity_classification_task", lambda agent: DummyTask())
    monkeypatch.setattr("crew_orchestrator.make_report_writer_task", lambda agent: DummyTask())
    monkeypatch.setattr("crew_orchestrator.Crew", lambda *args, **kwargs: type("DummyCrew", (), {"kickoff": lambda self, inputs: None})())

    def fake_parse_task_output(task, model):
        if model.__name__ == "FindingAnalysis":
            return FindingAnalysis(vulnerability_title="Test", vulnerability_type="Test", affected_components=[], attack_vector="Direct", evidence_summary="", technical_description="")
        if model.__name__ == "SeverityClassification":
            return SeverityClassification(severity="MEDIUM", cwe_ids=[], owasp_categories=[], wstg_categories=[], justification="")
        return ReportSection(title="Test", severity="MEDIUM", description="Test", affected_endpoints=[], steps_to_reproduce=[], remediation=[], references=[])

    monkeypatch.setattr("crew_orchestrator.parse_task_output", fake_parse_task_output)

    from crew_orchestrator import process_single_finding
    process_single_finding(
        "https://example.com",
        {"endpoint": "/api/users", "observation": "test", "evidence": "test"},
        object(),
        index=1,
        section_prefix="5",
        project_context=None,
    )

    assert captured["inputs"]["project_context"] == ""


def test_finding_analysis_task_includes_project_context_input():
    task = make_finding_analysis_task(None)
    description = task.description

    assert "{project_context}" in description
    assert "Project Context" in description
    assert "Raw finding JSON" in description
    assert "environmental context only" in description.lower()


def test_finding_analysis_task_reinforces_context_is_not_evidence():
    task = make_finding_analysis_task(None)
    description = task.description

    assert "tester-confirmed raw finding evidence" in description.lower()
    assert "project context" in description.lower()
    assert "never treat" in description.lower()
    assert "technology" in description.lower()
    assert "authentication" in description.lower()


def test_finding_analysis_schema_remains_compatible():
    result = FindingAnalysis(
        vulnerability_title="Exposed user data",
        vulnerability_type="Information disclosure",
        affected_components=["/api/users"],
        attack_vector="Direct API access",
        evidence_summary="HTTP 200 response with user data",
        technical_description="The API returned user profile data without authorization checks.",
        likely_cwe=None,
        likely_owasp=None,
        likely_wstg=None,
        assumptions=["Manual verification required"],
    )

    assert result.vulnerability_title == "Exposed user data"
    assert result.affected_components == ["/api/users"]
    assert result.model_dump()["likely_cwe"] is None


def test_finding_analysis_task_preserves_existing_json_output_behavior():
    task = make_finding_analysis_task(None)

    assert task.expected_output == JSON_SCHEMA_HINT.strip()
    assert "Return ONLY a valid JSON object" in task.description
    assert "Requires manual verification" in task.description


def test_severity_task_explicitly_accepts_project_context():
    task = make_severity_classification_task(None)
    description = task.description

    assert "{project_context}" in description
    assert "Project Context" in description
    assert "AI Analysis" in description
    assert "AI Classification" in description
    assert "Tester-confirmed evidence" in description or "tester-confirmed raw finding evidence" in description.lower()


def test_severity_task_uses_application_context_appropriately():
    task = make_severity_classification_task(None)
    description = task.description.lower()

    assert "application context" in description
    assert "technologies" in description
    assert "authentication" in description
    assert "roles" in description
    assert "context only" in description


def test_severity_task_prohibits_treating_project_context_as_vulnerability_evidence():
    task = make_severity_classification_task(None)
    description = task.description.lower()

    assert "not evidence of exploitation" in description or "never treat project context" in description
    assert "tester-provided evidence" in description or "tester-confirmed evidence" in description
    assert "never invent" in description or "do not invent" in description


def test_severity_task_requires_manual_verification_for_insufficient_evidence():
    task = make_severity_classification_task(None)
    description = task.description.lower()

    assert "requires manual verification" in description
    assert "insufficient evidence" in description or "evidence is insufficient" in description


def test_severity_task_prohibits_inventing_cvss_metrics():
    task = make_severity_classification_task(None)
    description = task.description.lower()

    assert "cvss" in description
    assert "do not invent" in description or "never invent" in description
    assert "cvss metrics" in description or "cvss" in description


def test_severity_schema_remains_compatible():
    result = SeverityClassification(
        severity="HIGH",
        cvss_score=7.5,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
        cwe_ids=["CWE-89"],
        owasp_categories=["Broken Access Control (OWASP A01:2025)"],
        wstg_categories=["Testing for Privilege Escalation (WSTG-ATHZ-03)"],
        justification="Evidence supports a high-severity issue with a clear user impact.",
    )

    assert result.severity == "HIGH"
    assert result.cvss_score == 7.5
    assert result.cwe_ids == ["CWE-89"]
    assert result.model_dump()["cvss_vector"] == "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N"


def test_report_writer_task_accepts_project_context():
    task = make_report_writer_task(None)
    description = task.description

    assert "{project_context}" in description
    assert "Project Context" in description
    assert "Raw finding JSON" in description
    assert "Finding Analysis" in description
    assert "Severity Classification" in description


def test_report_writer_task_uses_project_context_appropriately():
    task = make_report_writer_task(None)
    description = task.description.lower()

    assert "application context" in description
    assert "technologies" in description
    assert "authentication" in description
    assert "roles" in description
    assert "tailor" in description or "interpret" in description


def test_report_writer_task_prohibits_treating_project_context_as_evidence():
    task = make_report_writer_task(None)
    description = task.description.lower()

    assert "project context" in description
    assert "not vulnerability evidence" in description or "does not prove vulnerability" in description
    assert "tester-provided evidence" in description or "tester-confirmed" in description


def test_report_writer_task_preserves_tester_evidence_as_source_of_truth():
    task = make_report_writer_task(None)
    description = task.description.lower()

    assert "source of truth" in description
    assert "raw finding" in description
    assert "use only explicit evidence" in description or "use only confirmed facts" in description


def test_report_section_schema_remains_compatible():
    section = ReportSection(
        title="Insecure direct object reference",
        severity="HIGH",
        cvss_score=7.5,
        cwe="CWE-639",
        owasp="Broken Access Control (OWASP A01:2025)",
        wstg="Testing for Access Control (WSTG-ATHZ-03)",
        description="The endpoint returned a data object without authorization checks.",
        business_impact="User data may be disclosed.",
        affected_endpoints=[],
        steps_to_reproduce=["Call the endpoint with a valid token."],
        proof_of_concept="HTTP 200 response with user data.",
        remediation=["Enforce authorization checks before returning records."],
        remediation_recommendations=["Add role-based access validation."],
        references=["OWASP ASVS"],
        target="https://example.com",
        finding_id="VAPT-001",
        section_number="5.1",
    )

    assert section.title == "Insecure direct object reference"
    assert section.finding_id == "VAPT-001"
    assert section.section_number == "5.1"
    assert section.target == "https://example.com"
    assert section.remediation == ["Enforce authorization checks before returning records."]


def test_generate_vapt_report_rendering_remains_compatible(monkeypatch):
    monkeypatch.setattr("crew_orchestrator.get_llm", lambda **kwargs: object())

    def fake_process_single_finding(
        target,
        finding,
        llm,
        *,
        index,
        section_prefix,
        project_context=None,
    ):
        return ReportSection(
            title="Contextualized finding",
            severity="medium",
            description="Context-aware path",
            target=target,
            finding_id="VAPT-001",
            section_number="5.1",
            affected_endpoints=[],
            steps_to_reproduce=[],
            remediation=[],
            remediation_recommendations=[],
            references=[],
        )

    monkeypatch.setattr("crew_orchestrator.process_single_finding", fake_process_single_finding)

    result = __import__("crew_orchestrator", fromlist=["generate_vapt_report"]).generate_vapt_report({
        "target": "https://example.com",
        "finding": {
            "endpoint": "/api/users",
            "observation": "User data exposed",
            "evidence": "HTTP 200 response",
        },
    })

    assert result["target"] == "https://example.com"
    assert result["findings_count"] == 1
    assert "report_markdown" in result
    assert "docx_document" in result
    assert result["sections"][0]["title"] == "Contextualized finding"
