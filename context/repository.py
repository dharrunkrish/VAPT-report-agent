import json
from pathlib import Path
from typing import List, Optional

from context.models import ApplicationContext


class ContextRepository:
    """
    File-based repository for project application contexts.

    This is intentionally simple for Phase 1A.
    It can later be replaced by SQLite/PostgreSQL without
    changing the Context Manager interface.
    """

    def __init__(self, base_path: str = "projects"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _path(self, project_id: str) -> Path:
        safe_project_id = "".join(
            char if char.isalnum() or char in "-_" else "_"
            for char in project_id
        )

        return self.base_path / f"{safe_project_id}.json"

    def create(self, context: ApplicationContext) -> ApplicationContext:
        path = self._path(context.project_id)

        if path.exists():
            raise FileExistsError(
                f"Project already exists: {context.project_id}"
            )

        self._write(context)
        return context

    def get(self, project_id: str) -> Optional[ApplicationContext]:
        path = self._path(project_id)

        if not path.exists():
            return None

        data = json.loads(path.read_text(encoding="utf-8"))
        return ApplicationContext.model_validate(data)

    def update(self, context: ApplicationContext) -> ApplicationContext:
        path = self._path(context.project_id)

        if not path.exists():
            raise FileNotFoundError(
                f"Project does not exist: {context.project_id}"
            )

        self._write(context)
        return context

    def delete(self, project_id: str) -> bool:
        path = self._path(project_id)

        if not path.exists():
            return False

        path.unlink()
        return True

    def list_projects(self) -> List[str]:
        return sorted(
            path.stem
            for path in self.base_path.glob("*.json")
        )

    def _write(self, context: ApplicationContext) -> None:
        path = self._path(context.project_id)

        path.write_text(
            context.model_dump_json(indent=2),
            encoding="utf-8",
        )