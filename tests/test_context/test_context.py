from pathlib import Path

import pytest

from context import ApplicationContext, ContextManager, ContextRepository


def test_application_context_defaults():
    context = ApplicationContext(
        project_id="TEST-001",
        target="https://example.com",
    )

    assert context.project_id == "TEST-001"
    assert context.target == "https://example.com"
    assert context.scope == []
    assert context.technologies == []
    assert context.version == 1


def test_application_context_rejects_unknown_fields():
    with pytest.raises(Exception):
        ApplicationContext(
            project_id="TEST-001",
            target="https://example.com",
            unknown_field="invalid",
        )


def test_repository_create_get_delete(tmp_path: Path):
    repository = ContextRepository(str(tmp_path))

    context = ApplicationContext(
        project_id="TEST-001",
        target="https://example.com",
    )

    repository.create(context)

    loaded = repository.get("TEST-001")

    assert loaded is not None
    assert loaded.project_id == "TEST-001"

    assert repository.delete("TEST-001") is True
    assert repository.get("TEST-001") is None


def test_repository_prevents_duplicate_project(tmp_path: Path):
    repository = ContextRepository(str(tmp_path))

    context = ApplicationContext(
        project_id="TEST-001",
        target="https://example.com",
    )

    repository.create(context)

    with pytest.raises(FileExistsError):
        repository.create(context)


def test_context_manager_updates_version(tmp_path: Path):
    repository = ContextRepository(str(tmp_path))
    manager = ContextManager(repository)

    manager.create_project(
        project_id="TEST-001",
        target="https://example.com",
    )

    updated = manager.update_project(
        "TEST-001",
        {
            "technologies": ["REST API"]
        },
    )

    assert updated.version == 2
    assert updated.technologies == ["REST API"]


def test_context_manager_missing_project(tmp_path: Path):
    repository = ContextRepository(str(tmp_path))
    manager = ContextManager(repository)

    with pytest.raises(FileNotFoundError):
        manager.update_project(
            "DOES-NOT-EXIST",
            {"technologies": ["REST API"]},
        )