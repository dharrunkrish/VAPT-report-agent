import pytest

from context import ProjectFinding


def test_project_finding_defaults():
    finding = ProjectFinding(
        finding_id="VAPT-001",
        project_id="TEST-001",
    )

    assert finding.finding_id == "VAPT-001"
    assert finding.project_id == "TEST-001"
    assert finding.endpoint == ""
    assert finding.observation == ""
    assert finding.evidence == ""
    assert finding.status == "open"
    assert finding.review_status == "unreviewed"
    assert finding.ai_analysis is None
    assert finding.ai_severity is None
    assert finding.ai_remediation == []
    assert finding.confirmed_severity is None
    assert finding.confirmed_remediation == []
    assert finding.version == 1


def test_project_finding_accepts_existing_finding_fields():
    finding = ProjectFinding(
        finding_id="VAPT-001",
        project_id="TEST-001",
        endpoint="/api/users",
        observation="IDOR vulnerability",
        evidence="User A accessed User B data",
        notes="Tested with two accounts",
        request_evidence="GET /api/users/123",
        affected_roles="Authenticated User",
    )

    assert finding.endpoint == "/api/users"
    assert finding.observation == "IDOR vulnerability"
    assert finding.evidence == "User A accessed User B data"
    assert finding.notes == "Tested with two accounts"
    assert finding.request_evidence == "GET /api/users/123"
    assert finding.affected_roles == "Authenticated User"


def test_ai_analysis_is_stored_separately_from_tester_data():
    finding = ProjectFinding(
        finding_id="VAPT-001",
        project_id="TEST-001",
        ai_analysis="Likely broken access control due to missing authorization checks.",
    )

    assert finding.ai_analysis == "Likely broken access control due to missing authorization checks."
    assert finding.observation == ""
    assert finding.review_status == "unreviewed"


def test_ai_severity_and_ai_remediation_are_generated_without_confirmation():
    finding = ProjectFinding(
        finding_id="VAPT-001",
        project_id="TEST-001",
        ai_severity="HIGH",
        ai_remediation=["Enforce authorization checks.", "Validate object ownership before returning records."],
    )

    assert finding.ai_severity == "HIGH"
    assert finding.ai_remediation == [
        "Enforce authorization checks.",
        "Validate object ownership before returning records.",
    ]
    assert finding.confirmed_severity is None
    assert finding.confirmed_remediation == []
    assert finding.review_status == "unreviewed"


def test_reviewer_confirmation_state_is_explicit():
    finding = ProjectFinding(
        finding_id="VAPT-001",
        project_id="TEST-001",
        ai_severity="HIGH",
        ai_remediation=["Enforce authorization checks."],
        confirmed_severity="HIGH",
        confirmed_remediation=["Enforce authorization checks."],
        review_status="approved",
    )

    assert finding.review_status == "approved"
    assert finding.confirmed_severity == "HIGH"
    assert finding.confirmed_remediation == ["Enforce authorization checks."]


def test_reviewer_override_preserves_original_ai_recommendation():
    finding = ProjectFinding(
        finding_id="VAPT-001",
        project_id="TEST-001",
        ai_severity="HIGH",
        ai_remediation=["Enforce authorization checks."],
        confirmed_severity="CRITICAL",
        confirmed_remediation=["Enforce strict RBAC and ownership validation."],
        review_status="overridden",
    )

    assert finding.ai_severity == "HIGH"
    assert finding.confirmed_severity == "CRITICAL"
    assert finding.ai_remediation == ["Enforce authorization checks."]
    assert finding.confirmed_remediation == ["Enforce strict RBAC and ownership validation."]


def test_unreviewed_findings_reject_confirmed_values():
    with pytest.raises(ValueError, match="Unreviewed findings must not contain confirmed"):
        ProjectFinding(
            finding_id="VAPT-001",
            project_id="TEST-001",
            ai_severity="HIGH",
            confirmed_severity="HIGH",
        )


def test_legacy_finding_without_ai_fields_remains_valid():
    finding = ProjectFinding.model_validate(
        {
            "finding_id": "VAPT-001",
            "project_id": "TEST-001",
            "endpoint": "/api/users",
            "observation": "IDOR vulnerability",
            "evidence": "User A accessed User B data",
            "status": "open",
            "version": 1,
        }
    )

    assert finding.review_status == "unreviewed"
    assert finding.ai_analysis is None
    assert finding.ai_severity is None
    assert finding.ai_remediation == []
    assert finding.confirmed_severity is None
    assert finding.confirmed_remediation == []


def test_project_finding_serializes_and_deserializes_review_fields():
    finding = ProjectFinding(
        finding_id="VAPT-001",
        project_id="TEST-001",
        ai_analysis="Likely IDOR.",
        ai_severity="HIGH",
        ai_remediation=["Enforce authorization."],
        confirmed_severity="HIGH",
        confirmed_remediation=["Enforce authorization."],
        review_status="approved",
        review_notes="Reviewer confirmed the recommendation.",
    )

    payload = finding.model_dump()
    round_trip = ProjectFinding.model_validate(payload)

    assert round_trip.ai_analysis == "Likely IDOR."
    assert round_trip.ai_severity == "HIGH"
    assert round_trip.confirmed_severity == "HIGH"
    assert round_trip.review_status == "approved"
    assert round_trip.review_notes == "Reviewer confirmed the recommendation."


def test_project_finding_rejects_unknown_fields():
    with pytest.raises(Exception):
        ProjectFinding(
            finding_id="VAPT-001",
            project_id="TEST-001",
            unknown_field="invalid",
        )


def test_project_finding_version_can_be_updated():
    finding = ProjectFinding(
        finding_id="VAPT-001",
        project_id="TEST-001",
        version=2,
    )

    assert finding.version == 2
