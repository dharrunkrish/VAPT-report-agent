#!/usr/bin/env python3
"""FastAPI server exposing VAPTagen report generation to the frontend."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from api.response_mapper import section_to_api_response
from config.settings import OUTPUT_DIR, get_logger
from crew_orchestrator import generate_and_persist
from utils.schemas import ReportSection

logger = get_logger("api")

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


class GenerateFullRequest(BaseModel):
    target: str
    findings: List[FindingInput]
    section_prefix: Optional[str] = "5"


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


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=False)
