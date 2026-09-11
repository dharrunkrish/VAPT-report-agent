from pathlib import Path

import pytest

from context import FindingRepository, ProjectFinding


def make_finding(
    project_id="TEST-001",
    finding_id="VAPT-001",
):
    return ProjectFinding(
        project_id=project_id,
        finding_id=finding_id,
        endpoint="/api/users",
        observation="IDOR vulnerability",
        evidence="User A accessed User B data",
    )


def test_create_and_get_finding(tmp_path: Path):
    repository = FindingRepository(str(tmp_path))

    finding = make_finding()

    repository.create(finding)

    loaded = repository.get(
        "TEST-001",
        "VAPT-001",
    )

    assert loaded is not None
    assert loaded.project_id == "TEST-001"
    assert loaded.finding_id == "VAPT-001"
    assert loaded.observation == "IDOR vulnerability"


def test_repository_prevents_duplicate_finding(tmp_path: Path):
    repository = FindingRepository(str(tmp_path))

    finding = make_finding()

    repository.create(finding)

    with pytest.raises(FileExistsError):
        repository.create(finding)


def test_same_finding_id_allowed_in_different_projects(
    tmp_path: Path,
):
    repository = FindingRepository(str(tmp_path))

    finding_one = make_finding(
        project_id="TEST-001",
        finding_id="VAPT-001",
    )

    finding_two = make_finding(
        project_id="TEST-002",
        finding_id="VAPT-001",
    )

    repository.create(finding_one)
    repository.create(finding_two)

    assert repository.get("TEST-001", "VAPT-001") is not None
    assert repository.get("TEST-002", "VAPT-001") is not None


def test_update_finding(tmp_path: Path):
    repository = FindingRepository(str(tmp_path))

    finding = make_finding()

    repository.create(finding)

    updated = finding.model_copy(
        update={
            "observation": "Updated observation",
            "version": 2,
        }
    )

    repository.update(updated)

    loaded = repository.get(
        "TEST-001",
        "VAPT-001",
    )

    assert loaded is not None
    assert loaded.observation == "Updated observation"
    assert loaded.version == 2


def test_update_missing_finding(tmp_path: Path):
    repository = FindingRepository(str(tmp_path))

    with pytest.raises(FileNotFoundError):
        repository.update(make_finding())


def test_delete_finding(tmp_path: Path):
    repository = FindingRepository(str(tmp_path))

    repository.create(make_finding())

    assert repository.delete(
        "TEST-001",
        "VAPT-001",
    ) is True

    assert repository.get(
        "TEST-001",
        "VAPT-001",
    ) is None


def test_delete_missing_finding(tmp_path: Path):
    repository = FindingRepository(str(tmp_path))

    assert repository.delete(
        "TEST-001",
        "VAPT-001",
    ) is False


def test_list_project_findings(tmp_path: Path):
    repository = FindingRepository(str(tmp_path))

    repository.create(
        make_finding(
            project_id="TEST-001",
            finding_id="VAPT-002",
        )
    )

    repository.create(
        make_finding(
            project_id="TEST-001",
            finding_id="VAPT-001",
        )
    )

    repository.create(
        make_finding(
            project_id="TEST-002",
            finding_id="VAPT-001",
        )
    )

    assert repository.list_findings("TEST-001") == [
        "VAPT-001",
        "VAPT-002",
    ]

    assert repository.list_findings("TEST-002") == [
        "VAPT-001",
    ]
