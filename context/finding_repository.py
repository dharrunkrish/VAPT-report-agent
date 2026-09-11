import json
from pathlib import Path
from typing import List, Optional

from context.finding_models import ProjectFinding


class FindingRepository:
    """
    File-based repository for project findings.

    Findings are stored under a project-specific directory so that
    finding IDs are unique within a project rather than globally.
    """

    def __init__(self, base_path: str = "findings"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _project_path(self, project_id: str) -> Path:
        safe_project_id = "".join(
            char if char.isalnum() or char in "-_" else "_"
            for char in project_id
        )

        path = self.base_path / safe_project_id
        path.mkdir(parents=True, exist_ok=True)

        return path

    def _path(self, project_id: str, finding_id: str) -> Path:
        safe_finding_id = "".join(
            char if char.isalnum() or char in "-_" else "_"
            for char in finding_id
        )

        return self._project_path(project_id) / f"{safe_finding_id}.json"

    def create(self, finding: ProjectFinding) -> ProjectFinding:
        path = self._path(
            finding.project_id,
            finding.finding_id,
        )

        if path.exists():
            raise FileExistsError(
                f"Finding already exists: "
                f"{finding.project_id}/{finding.finding_id}"
            )

        self._write(finding)
        return finding

    def get(
        self,
        project_id: str,
        finding_id: str,
    ) -> Optional[ProjectFinding]:

        path = self._path(project_id, finding_id)

        if not path.exists():
            return None

        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        return ProjectFinding.model_validate(data)

    def update(self, finding: ProjectFinding) -> ProjectFinding:
        path = self._path(
            finding.project_id,
            finding.finding_id,
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Finding does not exist: "
                f"{finding.project_id}/{finding.finding_id}"
            )

        self._write(finding)
        return finding

    def delete(
        self,
        project_id: str,
        finding_id: str,
    ) -> bool:

        path = self._path(project_id, finding_id)

        if not path.exists():
            return False

        path.unlink()
        return True

    def list_findings(
        self,
        project_id: str,
    ) -> List[str]:

        project_path = self._project_path(project_id)

        return sorted(
            path.stem
            for path in project_path.glob("*.json")
        )

    def _write(self, finding: ProjectFinding) -> None:
        path = self._path(
            finding.project_id,
            finding.finding_id,
        )

        path.write_text(
            finding.model_dump_json(indent=2),
            encoding="utf-8",
        )
