from typing import Any, Dict, Optional

from context.models import ApplicationContext
from context.repository import ContextRepository
from context.finding_models import ProjectFinding
from context.finding_repository import FindingRepository
import json

from crewai import Crew, Process

from agents import (
    make_finding_analysis_agent,
    make_severity_agent,
    make_report_writer_agent,
)
from tasks import (
    make_finding_analysis_task,
    make_severity_classification_task,
    make_report_writer_task,
)
from utils.parser import parse_task_output
from utils.schemas import FindingAnalysis, SeverityClassification, ReportSection
from utils.llm import get_llm


class ContextManager:
    """
    Application-level interface for managing shared VAPT context.
    """

    def __init__(
        self,
        repository: Optional[ContextRepository] = None,
        finding_repository: Optional[FindingRepository] = None,
    ):
        self.repository = repository or ContextRepository()
        self.finding_repository = finding_repository or FindingRepository()

    def create_finding(
        self,
        finding_id: str,
        project_id: str,
        *,
        endpoint: str = "",
        observation: str = "",
        evidence: str = "",
        notes: Optional[str] = None,
        request_evidence: Optional[str] = None,
        affected_roles: Optional[str] = None,
    ) -> ProjectFinding:

        project = self.repository.get(project_id)

        if project is None:
            raise FileNotFoundError(
                f"Project does not exist: {project_id}"
            )

        finding = ProjectFinding(
            finding_id=finding_id,
            project_id=project_id,
            endpoint=endpoint,
            observation=observation,
            evidence=evidence,
            notes=notes,
            request_evidence=request_evidence,
            affected_roles=affected_roles,
        )

        return self.finding_repository.create(finding)


    def get_finding(
        self,
        project_id: str,
        finding_id: str,
    ) -> Optional[ProjectFinding]:

        return self.finding_repository.get(
            project_id,
            finding_id,
        )


    def update_finding(
        self,
        project_id: str,
        finding_id: str,
        updates: Dict[str, Any],
    ) -> ProjectFinding:

        current = self.finding_repository.get(
            project_id,
            finding_id,
        )

        if current is None:
            raise FileNotFoundError(
                f"Finding does not exist: "
                f"{project_id}/{finding_id}"
            )

        data = current.model_dump()
        data.update(updates)

        # Prevent changing ownership through an update.
        data["project_id"] = project_id
        data["finding_id"] = finding_id
        data["version"] = current.version + 1

        updated = ProjectFinding.model_validate(data)

        return self.finding_repository.update(updated)


    def delete_finding(
        self,
        project_id: str,
        finding_id: str,
    ) -> bool:

        return self.finding_repository.delete(
            project_id,
            finding_id,
        )


    def list_findings(
        self,
        project_id: str,
    ) -> list[str]:

        project = self.repository.get(project_id)

        if project is None:
            raise FileNotFoundError(
                f"Project does not exist: {project_id}"
            )

        return self.finding_repository.list_findings(project_id)
    
    def create_project(
        self,
        project_id: str,
        target: str,
        *,
        scope: Optional[list[str]] = None,
        technologies: Optional[list[str]] = None,
        authentication: Optional[Dict[str, Any]] = None,
        roles: Optional[list[str]] = None,
        assets: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> ApplicationContext:

        context = ApplicationContext(
            project_id=project_id,
            target=target,
            scope=scope or [],
            technologies=technologies or [],
            authentication=authentication or {},
            roles=roles or [],
            assets=assets or [],
            notes=notes,
        )

        return self.repository.create(context)

    def get_project(
        self,
        project_id: str,
    ) -> Optional[ApplicationContext]:

        return self.repository.get(project_id)

    def update_project(
        self,
        project_id: str,
        updates: Dict[str, Any],
    ) -> ApplicationContext:

        current = self.repository.get(project_id)

        if current is None:
            raise FileNotFoundError(
                f"Project does not exist: {project_id}"
            )

        data = current.model_dump()

        data.update(updates)

        data["version"] = current.version + 1

        updated = ApplicationContext.model_validate(data)

        return self.repository.update(updated)

    def delete_project(self, project_id: str) -> bool:
        return self.repository.delete(project_id)

    def list_projects(self) -> list[str]:
        return self.repository.list_projects()

    def generate_finding_intelligence(
        self,
        project_id: str,
        finding_id: str,
        llm=None,
    ) -> ProjectFinding:
        """
        Run the context-aware AI pipeline to generate analysis, severity,
        and remediation recommendations for a single finding and persist
        the AI-generated intelligence on the finding record.

        This method is idempotent and will not overwrite reviewer-confirmed
        values. It only updates AI recommendation fields when no reviewer
        confirmed values exist for the finding.
        """

        project = self.repository.get(project_id)

        if project is None:
            raise FileNotFoundError(f"Project does not exist: {project_id}")

        finding = self.finding_repository.get(project_id, finding_id)

        if finding is None:
            raise FileNotFoundError(f"Finding does not exist: {project_id}/{finding_id}")

        # Prepare serialized inputs for the AI tasks
        project_context = json.dumps(project.model_dump(), ensure_ascii=False, sort_keys=True)
        finding_json = json.dumps(finding.model_dump(), ensure_ascii=False)

        # Build agents and tasks
        analysis_agent = make_finding_analysis_agent(llm=llm or get_llm(temperature=0.15))
        severity_agent = make_severity_agent(llm=llm or get_llm(temperature=0.1))
        writer_agent = make_report_writer_agent(llm=llm or get_llm(temperature=0.1))

        analysis_task = make_finding_analysis_task(analysis_agent)
        severity_task = make_severity_classification_task(severity_agent)
        report_task = make_report_writer_task(writer_agent)

        severity_task.context = [analysis_task]
        report_task.context = [analysis_task, severity_task]

        crew = Crew(
            agents=[analysis_agent, severity_agent, writer_agent],
            tasks=[analysis_task, severity_task, report_task],
            process=Process.sequential,
            verbose=False,
            memory=False,
        )

        inputs = {
            "target": project.target,
            "finding": finding_json,
            "analysis": "Use the previous finding-analysis output and keep it distinct from raw tester evidence.",
            "severity": "Use the severity classification output and distinguish it from raw tester evidence.",
            "project_context": project_context,
        }

        # Run the AI pipeline. If anything fails, do not persist partial results.
        try:
            crew.kickoff(inputs=inputs)

            analysis = parse_task_output(analysis_task, FindingAnalysis)
            severity = parse_task_output(severity_task, SeverityClassification)
            section = parse_task_output(report_task, ReportSection)

        except Exception as exc:
            # Fail safely without modifying the finding
            raise RuntimeError(f"AI generation failed: {exc}") from exc

        # Prepare new AI-derived values
        ai_analysis_str = json.dumps(analysis.model_dump(), ensure_ascii=False)
        ai_severity_val = (severity.severity or "").upper()
        ai_remediation_list = section.remediation_items() or []

        # Determine whether reviewer-confirmed values exist; if they do, preserve
        # existing AI recommendation and reviewer values.
        has_confirmed = bool(finding.confirmed_severity or finding.confirmed_remediation)

        updates: dict = {}

        if not has_confirmed:
            updates["ai_analysis"] = ai_analysis_str
            updates["ai_severity"] = ai_severity_val
            updates["ai_remediation"] = ai_remediation_list
            # Ensure unreviewed state for newly generated AI recommendations
            updates["review_status"] = "unreviewed"

        # Always preserve tester-provided fields by not touching them.

        if not updates:
            # Nothing to persist (reviewer has already confirmed/overridden)
            return finding

        # Persist updates via existing update_finding path (handles versioning/validation)
        try:
            updated = self.update_finding(project_id, finding_id, updates)
        except Exception as exc:
            # Surface meaningful error without corrupting existing data
            raise RuntimeError(f"Failed to persist AI intelligence: {exc}") from exc

        return updated

    def review_finding(
        self,
        project_id: str,
        finding_id: str,
        *,
        severity_action: str | None = None,
        severity: str | None = None,
        remediation_action: str | None = None,
        remediation: list[str] | None = None,
    ) -> ProjectFinding:
        """
        Apply reviewer confirmation/override actions atomically to a finding.

        severity_action: 'approve' to accept the current ai_severity; 'override' to set a new confirmed_severity.
        remediation_action: 'approve' to accept ai_remediation; 'override' to set confirmed_remediation.
        """

        allowed_actions = {None, "approve", "override"}
        if severity_action not in allowed_actions:
            raise ValueError("Invalid severity_action")
        if remediation_action not in allowed_actions:
            raise ValueError("Invalid remediation_action")

        project = self.repository.get(project_id)
        if project is None:
            raise FileNotFoundError(f"Project does not exist: {project_id}")

        finding = self.finding_repository.get(project_id, finding_id)
        if finding is None:
            raise FileNotFoundError(f"Finding does not exist: {project_id}/{finding_id}")

        # Supported severities (case-insensitive for validation)
        SUPPORTED = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL", "Requires manual verification"}

        updates: dict = {}

        # Severity handling
        if severity_action == "approve":
            if not finding.ai_severity:
                raise ValueError("No AI severity available to approve")
            updates["confirmed_severity"] = finding.ai_severity

        if severity_action == "override":
            if not severity or not str(severity).strip():
                raise ValueError("Override severity must be provided")
            sev_up = str(severity).strip()
            if sev_up.upper() not in {s.upper() for s in SUPPORTED}:
                raise ValueError(f"Invalid severity: {sev_up}")
            updates["confirmed_severity"] = sev_up

        # Remediation handling
        if remediation_action == "approve":
            if not finding.ai_remediation:
                raise ValueError("No AI remediation available to approve")
            updates["confirmed_remediation"] = finding.ai_remediation

        if remediation_action == "override":
            if not remediation:
                raise ValueError("Remediation override must be a non-empty list")
            if not isinstance(remediation, list) or not all(isinstance(r, str) and r.strip() for r in remediation):
                raise ValueError("Remediation override must be a list of non-empty strings")
            updates["confirmed_remediation"] = [r.strip() for r in remediation]

        if not updates:
            raise ValueError("No review action provided")

        # Determine new review_status
        new_confirmed_severity = updates.get("confirmed_severity", finding.confirmed_severity)
        new_confirmed_remediation = updates.get("confirmed_remediation", finding.confirmed_remediation)

        # Determine if overrides (confirmed value differs from AI recommendation)
        is_overridden = False
        if new_confirmed_severity and finding.ai_severity and new_confirmed_severity != finding.ai_severity:
            is_overridden = True
        if new_confirmed_remediation and finding.ai_remediation and new_confirmed_remediation != finding.ai_remediation:
            is_overridden = True

        if is_overridden:
            updates["review_status"] = "overridden"
        else:
            # If both confirmed fields exist and (match AI if AI exists), mark approved
            both_confirmed = bool(new_confirmed_severity) and bool(new_confirmed_remediation)
            matches_ai = True
            if finding.ai_severity and new_confirmed_severity and finding.ai_severity != new_confirmed_severity:
                matches_ai = False
            if finding.ai_remediation and new_confirmed_remediation and finding.ai_remediation != new_confirmed_remediation:
                matches_ai = False

            if both_confirmed and matches_ai:
                updates["review_status"] = "approved"
            else:
                updates["review_status"] = "reviewed"

        # Persist atomically via update_finding (which handles validation/versioning)
        try:
            updated = self.update_finding(project_id, finding_id, updates)
        except Exception as exc:
            raise RuntimeError(f"Failed to persist review updates: {exc}") from exc

        return updated