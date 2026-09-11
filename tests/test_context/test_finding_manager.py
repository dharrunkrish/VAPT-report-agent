from pathlib import Path

import pytest

from context import (
    ContextManager,
    ContextRepository,
    FindingRepository,
)


def make_manager(tmp_path: Path) -> ContextManager:
    repository = ContextRepository(
        str(tmp_path / "projects")
    )

    finding_repository = FindingRepository(
        str(tmp_path / "findings")
    )

    manager = ContextManager(
        repository=repository,
        finding_repository=finding_repository,
    )

    manager.create_project(
        project_id="TEST-001",
        target="https://example.com",
    )

    return manager


def test_create_and_get_finding(tmp_path: Path):
    manager = make_manager(tmp_path)

    finding = manager.create_finding(
        finding_id="VAPT-001",
        project_id="TEST-001",
        endpoint="/api/users",
        observation="IDOR vulnerability",
        evidence="User A accessed User B data",
    )

    assert finding.finding_id == "VAPT-001"
    assert finding.project_id == "TEST-001"

    loaded = manager.get_finding(
        "TEST-001",
        "VAPT-001",
    )

    assert loaded is not None
    assert loaded.observation == "IDOR vulnerability"


def test_create_finding_requires_existing_project(
    tmp_path: Path,
):
    repository = ContextRepository(
        str(tmp_path / "projects")
    )

    finding_repository = FindingRepository(
        str(tmp_path / "findings")
    )

    manager = ContextManager(
        repository=repository,
        finding_repository=finding_repository,
    )

    with pytest.raises(FileNotFoundError):
        manager.create_finding(
            finding_id="VAPT-001",
            project_id="DOES-NOT-EXIST",
        )


def test_duplicate_finding_rejected(tmp_path: Path):
    manager = make_manager(tmp_path)

    manager.create_finding(
        finding_id="VAPT-001",
        project_id="TEST-001",
    )

    with pytest.raises(FileExistsError):
        manager.create_finding(
            finding_id="VAPT-001",
            project_id="TEST-001",
        )


def test_update_finding_increments_version(
    tmp_path: Path,
):
    manager = make_manager(tmp_path)

    manager.create_finding(
        finding_id="VAPT-001",
        project_id="TEST-001",
        observation="Original",
    )

    updated = manager.update_finding(
        "TEST-001",
        "VAPT-001",
        {
            "observation": "Updated",
        },
    )

    assert updated.observation == "Updated"
    assert updated.version == 2


def test_update_finding_cannot_change_project(
    tmp_path: Path,
):
    manager = make_manager(tmp_path)

    manager.create_finding(
        finding_id="VAPT-001",
        project_id="TEST-001",
    )

    updated = manager.update_finding(
        "TEST-001",
        "VAPT-001",
        {
            "project_id": "TEST-999",
        },
    )

    assert updated.project_id == "TEST-001"


def test_missing_finding_update_rejected(
    tmp_path: Path,
):
    manager = make_manager(tmp_path)

    with pytest.raises(FileNotFoundError):
        manager.update_finding(
            "TEST-001",
            "VAPT-999",
            {"observation": "Updated"},
        )


def test_list_findings_requires_existing_project(
    tmp_path: Path,
):
    manager = make_manager(tmp_path)

    manager.create_finding(
        finding_id="VAPT-002",
        project_id="TEST-001",
    )

    manager.create_finding(
        finding_id="VAPT-001",
        project_id="TEST-001",
    )

    assert manager.list_findings("TEST-001") == [
        "VAPT-001",
        "VAPT-002",
    ]

    with pytest.raises(FileNotFoundError):
        manager.list_findings("DOES-NOT-EXIST")


def test_delete_finding(tmp_path: Path):
    manager = make_manager(tmp_path)

    manager.create_finding(
        finding_id="VAPT-001",
        project_id="TEST-001",
    )

    assert manager.delete_finding(
        "TEST-001",
        "VAPT-001",
    ) is True

    assert manager.get_finding(
        "TEST-001",
        "VAPT-001",
    ) is None
