from typing import Any, Dict, Optional

from context.manager import ContextManager


class ProjectContextService:
    """
    Retrieves and assembles project context with a specific finding.

    This service only handles context retrieval. AI-generated severity,
    remediation, and report content are intentionally kept separate.
    """

    def __init__(self, manager: Optional[ContextManager] = None):
        self.manager = manager or ContextManager()

    def get_finding_context(
        self,
        project_id: str,
        finding_id: str,
    ) -> Dict[str, Any]:
        project = self.manager.get_project(project_id)

        if project is None:
            raise FileNotFoundError(
                f"Project '{project_id}' not found."
            )

        finding = self.manager.get_finding(project_id, finding_id)

        if finding is None:
            raise FileNotFoundError(
                f"Finding '{finding_id}' not found in project '{project_id}'."
            )

        # Compute "effective" values used by downstream reporting without
        # modifying stored records: prefer reviewer-confirmed values when
        # present, otherwise fall back to AI recommendations. Preserve the
        # original `ai_*` and `confirmed_*` fields in the returned dict.
        finding_data = finding.model_dump()

        effective_severity = finding.confirmed_severity or finding.ai_severity
        effective_remediation = finding.confirmed_remediation or finding.ai_remediation or []

        # Expose effective values under common keys so report generation and
        # downstream consumers can read a single `severity`/`remediation` field.
        finding_data["severity"] = effective_severity
        finding_data["remediation"] = effective_remediation

        return {
            "project_context": project.model_dump(),
            "finding": finding_data,
        }
