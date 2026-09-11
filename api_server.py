#!/usr/bin/env python3
"""FastAPI server exposing VAPTagen report generation to the frontend."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import crew_orchestrator
from api.response_mapper import section_to_api_response
from config.settings import OUTPUT_DIR, get_logger
from context.service import ProjectContextService
from crew_orchestrator import generate_and_persist
from utils.schemas import ReportSection
from context import ApplicationContext, ContextManager, ProjectFinding

logger = get_logger("api")

context_manager = ContextManager()

app = FastAPI(
    title="VAPTagen API",
    description="AI-powered VAPT report generation",
    version="1.0.0",
)

_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:8080,http://127.0.0.1:5173,http://127.0.0.1:8080,http://192.168.0.9:8080",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FindingInput(BaseModel):
    endpoint: str = ""
    observation: str = ""
    evidence: str = ""
    notes: Optional[str] = None
    request_evidence: Optional[str] = None
    affected_roles: Optional[str] = None

class CreateProjectRequest(BaseModel):
    project_id: str
    target: str
    scope: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    authentication: Dict[str, Any] = Field(default_factory=dict)
    roles: List[str] = Field(default_factory=list)
    assets: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

class CreateFindingRequest(BaseModel):
    finding_id: str
    endpoint: str = ""
    observation: str = ""
    evidence: str = ""
    notes: Optional[str] = None
    request_evidence: Optional[str] = None
    affected_roles: Optional[str] = None

class UpdateFindingRequest(BaseModel):
    endpoint: Optional[str] = None
    observation: Optional[str] = None
    evidence: Optional[str] = None
    notes: Optional[str] = None
    request_evidence: Optional[str] = None
    affected_roles: Optional[str] = None
    status: Optional[str] = None

class GenerateReportRequest(BaseModel):
    target: str
    finding: FindingInput
    section_prefix: Optional[str] = "5"


class GenerateReportResponse(BaseModel):
    title: str
    severity: str
    owasp: str
    cwe: str
    wstg: str = ""
    description: str
    technical_impact: str
    business_impact: str
    steps_to_reproduce: List[str]
    proof_of_concept: str
    remediation: List[str]
    references: List[str] = Field(default_factory=list)
    finding_id: Optional[str] = None
    section_number: Optional[str] = None
    cvss_score: Optional[float] = None
    affected_endpoints: List[Dict[str, Any]] = Field(default_factory=list)
    markdown: str = ""
    markdown_filename: Optional[str] = None
    docx_filename: Optional[str] = None
    json_filename: Optional[str] = None


@app.get("/health")

def health() -> Dict[str, str]:
    return {"status": "ok", "service": "vaptagen"}

@app.post("/projects", response_model=ApplicationContext)
def create_project(body: CreateProjectRequest) -> ApplicationContext:
    """Create a new VAPT project with shared application context."""

    try:
        if not body.project_id.strip():
            raise HTTPException(
                status_code=400,
                detail="project_id is required",
            )

        if not body.target.strip():
            raise HTTPException(
                status_code=400,
                detail="target is required",
            )

        project = context_manager.create_project(
            project_id=body.project_id.strip(),
            target=body.target.strip(),
            scope=body.scope,
            technologies=body.technologies,
            authentication=body.authentication,
            roles=body.roles,
            assets=body.assets,
            notes=body.notes,
        )

        logger.info(
            "Created project context project_id=%s target=%s",
            project.project_id,
            project.target,
        )

        return project

    except FileExistsError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except HTTPException:
        # Re-raise HTTP errors (e.g. validation) so they are returned as-is.
        raise

    except Exception as exc:
        logger.exception("Project creation failed")
        raise HTTPException(
            status_code=500,
            detail=f"Project creation failed: {exc}",
        ) from exc


@app.get("/projects/{project_id}", response_model=ApplicationContext)
def get_project(project_id: str) -> ApplicationContext:
    """Retrieve shared application context for a project."""

    project = context_manager.get_project(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project not found: {project_id}",
        )

    return project

class GenerateFullRequest(BaseModel):
    target: str
    findings: List[FindingInput]
    section_prefix: Optional[str] = "5"


class ReviewRequest(BaseModel):
    severity_action: Optional[str] = None  # 'approve' | 'override'
    severity: Optional[str] = None
    remediation_action: Optional[str] = None  # 'approve' | 'override'
    remediation: Optional[List[str]] = None


def _build_api_response(persisted: Dict[str, Any]) -> GenerateReportResponse:
    sections = persisted.get("sections") or []
    if not sections:
        raise HTTPException(status_code=500, detail="No report section generated")

    section = ReportSection.model_validate(sections[0])
    api_data = section_to_api_response(section)

    docx_path = Path(persisted.get("report_docx_path", ""))
    md_path = Path(persisted.get("report_markdown_path", ""))
    json_path = Path(persisted.get("findings_json_path", ""))

    api_data["markdown"] = persisted.get("report_markdown") or ""
    api_data["docx_filename"] = docx_path.name if docx_path.exists() else None
    api_data["markdown_filename"] = md_path.name if md_path.exists() else None
    api_data["json_filename"] = json_path.name if json_path.exists() else None
    return GenerateReportResponse(**api_data)

@app.post(
    "/projects/{project_id}/findings",
    response_model=ProjectFinding,
)
def create_finding(
    project_id: str,
    body: CreateFindingRequest,
) -> ProjectFinding:
    """Create a finding under an existing VAPT project."""

    try:
        if not body.finding_id.strip():
            raise HTTPException(
                status_code=400,
                detail="finding_id is required",
            )

        finding = context_manager.create_finding(
            finding_id=body.finding_id.strip(),
            project_id=project_id,
            endpoint=body.endpoint,
            observation=body.observation,
            evidence=body.evidence,
            notes=body.notes,
            request_evidence=body.request_evidence,
            affected_roles=body.affected_roles,
        )

        logger.info(
            "Created finding project_id=%s finding_id=%s",
            project_id,
            finding.finding_id,
        )

        return finding

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except FileExistsError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Finding creation failed")
        raise HTTPException(
            status_code=500,
            detail=f"Finding creation failed: {exc}",
        ) from exc

@app.get(
    "/projects/{project_id}/findings",
    response_model=List[str],
)
def list_findings(project_id: str) -> List[str]:
    """List finding IDs belonging to a project."""

    try:
        return context_manager.list_findings(project_id)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Finding listing failed")
        raise HTTPException(
            status_code=500,
            detail=f"Finding listing failed: {exc}",
        ) from exc

@app.get(
    "/projects/{project_id}/findings/{finding_id}",
    response_model=ProjectFinding,
)
def get_finding(
    project_id: str,
    finding_id: str,
) -> ProjectFinding:
    """Retrieve a finding belonging to a project."""

    finding = context_manager.get_finding(
        project_id,
        finding_id,
    )

    if finding is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Finding not found: "
                f"{project_id}/{finding_id}"
            ),
        )

    return finding

@app.put(
    "/projects/{project_id}/findings/{finding_id}",
    response_model=ProjectFinding,
)
def update_finding(
    project_id: str,
    finding_id: str,
    body: UpdateFindingRequest,
) -> ProjectFinding:
    """Update a project finding."""

    updates = body.model_dump(
        exclude_unset=True,
    )

    try:
        return context_manager.update_finding(
            project_id,
            finding_id,
            updates,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Finding update failed")
        raise HTTPException(
            status_code=500,
            detail=f"Finding update failed: {exc}",
        ) from exc

@app.delete(
    "/projects/{project_id}/findings/{finding_id}",
)
def delete_finding(
    project_id: str,
    finding_id: str,
) -> Dict[str, Any]:
    """Delete a finding from a project."""

    deleted = context_manager.delete_finding(
        project_id,
        finding_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Finding not found: "
                f"{project_id}/{finding_id}"
            ),
        )

    return {
        "deleted": True,
        "project_id": project_id,
        "finding_id": finding_id,
    }

@app.post(
    "/projects/{project_id}/findings/{finding_id}/generate",
    response_model=GenerateReportResponse,
)
def generate_project_finding_report(project_id: str, finding_id: str) -> GenerateReportResponse:
    """Generate a report for a finding that belongs to a project using the context-aware pipeline."""
    project = context_manager.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    finding = context_manager.get_finding(project_id, finding_id)
    if finding is None:
        raise HTTPException(
            status_code=404,
            detail=f"Finding not found: {project_id}/{finding_id}",
        )

    project_context_service = ProjectContextService(context_manager)
    combined_context = project_context_service.get_finding_context(project_id, finding_id)
    if not combined_context.get("project_context") or not combined_context.get("finding"):
        raise HTTPException(status_code=404, detail=f"Context not found for {project_id}/{finding_id}")

    crew_orchestrator.set_project_context_service(project_context_service)

    payload = {
        "target": project.target,
        "project_id": project_id,
        "finding_id": finding_id,
        "finding": combined_context["finding"],
    }
    logger.info("API project-scoped report target=%s project_id=%s finding_id=%s", project.target, project_id, finding_id)

    try:
        persisted = generate_and_persist(payload)
        return _build_api_response(persisted)

    except HTTPException:
        raise
    except EnvironmentError as exc:
        logger.error("Configuration error: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Report generation failed")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}") from exc


@app.post(
    "/projects/{project_id}/findings/{finding_id}/intelligence",
    response_model=ProjectFinding,
)
def generate_project_finding_intelligence(project_id: str, finding_id: str) -> ProjectFinding:
    """
    Generate AI intelligence (analysis, severity recommendation, remediation)
    for an existing finding and persist the AI-generated values separately
    from any reviewer-confirmed values.
    """
    project = context_manager.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    finding = context_manager.get_finding(project_id, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail=f"Finding not found: {project_id}/{finding_id}")

    try:
        updated = context_manager.generate_finding_intelligence(project_id, finding_id)
        return updated

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Intelligence generation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Intelligence generation failed")
        raise HTTPException(status_code=500, detail=f"Intelligence generation failed: {exc}") from exc


@app.post("/generate-report", response_model=GenerateReportResponse)
def generate_report(body: GenerateReportRequest) -> GenerateReportResponse:
    payload = body.model_dump()
    logger.info("API generate-report target=%s", body.target)

    try:
        if not body.target.strip():
            raise HTTPException(status_code=400, detail="target is required")

        persisted = generate_and_persist(payload)
        return _build_api_response(persisted)

    except HTTPException:
        raise
    except EnvironmentError as exc:
        logger.error("Configuration error: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Report generation failed")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}") from exc


@app.post("/generate", response_model=GenerateReportResponse)
def generate_full_report(body: GenerateFullRequest) -> GenerateReportResponse:
    """CrewAI pipeline entry point used by the Report Generation page."""
    payload = {
        "target": body.target,
        "findings": [f.model_dump() for f in body.findings],
        "section_prefix": body.section_prefix,
    }
    logger.info("API /generate target=%s findings=%s", body.target, len(body.findings))

    try:
        if not body.target.strip():
            raise HTTPException(status_code=400, detail="target is required")
        if not body.findings:
            raise HTTPException(status_code=400, detail="findings array is required")

        persisted = generate_and_persist(payload)
        return _build_api_response(persisted)

    except HTTPException:
        raise
    except EnvironmentError as exc:
        logger.error("Configuration error: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Report generation failed")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}") from exc


@app.get("/files/{filename}")
def download_file(filename: str) -> FileResponse:
    safe_name = Path(filename).name
    filepath = Path(OUTPUT_DIR) / safe_name

    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    media = "application/octet-stream"
    if safe_name.endswith(".docx"):
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif safe_name.endswith(".md"):
        media = "text/markdown"
    elif safe_name.endswith(".json"):
        media = "application/json"

    return FileResponse(path=str(filepath), filename=safe_name, media_type=media)


@app.patch(
    "/projects/{project_id}/findings/{finding_id}/review",
    response_model=ProjectFinding,
)
def review_project_finding(project_id: str, finding_id: str, body: ReviewRequest) -> ProjectFinding:
    """
    Apply reviewer confirmation or override to a finding's AI recommendations.
    """
    project = context_manager.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    finding = context_manager.get_finding(project_id, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail=f"Finding not found: {project_id}/{finding_id}")

    # Basic payload validation: at least one action
    if not any([body.severity_action, body.remediation_action]):
        raise HTTPException(status_code=400, detail="At least one review action must be provided")

    try:
        updated = context_manager.review_finding(
            project_id,
            finding_id,
            severity_action=body.severity_action,
            severity=body.severity,
            remediation_action=body.remediation_action,
            remediation=body.remediation,
        )
        return updated

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Review update failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Review update failed")
        raise HTTPException(status_code=500, detail=f"Review update failed: {exc}") from exc


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=False)
