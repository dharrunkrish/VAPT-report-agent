import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from crewai import Crew, Process

from agents import (
    make_exec_summary_agent,
    make_finding_analysis_agent,
    make_report_writer_agent,
    make_severity_agent,
)
from config.report_styles import DEFAULT_SECTION_PREFIX
from config.settings import get_logger
from tasks import (
    make_executive_summary_task,
    make_finding_analysis_task,
    make_report_writer_task,
    make_severity_classification_task,
)
from utils.docx_report import build_vapt_docx
from utils.llm import get_llm
from utils.output import save_docx, save_findings_json, save_markdown
from utils.parser import parse_task_output
from utils.render import render_full_report
from utils.schemas import (
    ExecutiveSummary,
    FindingAnalysis,
    ReportSection,
    SeverityClassification,
    enrich_report_section,
)

logger = get_logger("orchestrator")


def normalize_input(payload: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]], str]:
    target = str(payload.get("target", "")).strip()
    section_prefix = str(payload.get("section_prefix", DEFAULT_SECTION_PREFIX)).strip()

    if "finding" in payload:
        finding = payload["finding"]
        if not isinstance(finding, dict):
            raise ValueError("'finding' must be a JSON object.")
        return target, [finding], section_prefix

    if "findings" in payload:
        findings = payload["findings"]
        if not isinstance(findings, list) or not findings:
            raise ValueError("'findings' must be a non-empty array.")
        for idx, item in enumerate(findings, 1):
            if not isinstance(item, dict):
                raise ValueError(f"Finding #{idx} must be a JSON object.")
        return target, findings, section_prefix

    if any(k in payload for k in ("endpoint", "observation", "evidence", "title")):
        return target, [payload], section_prefix

    raise ValueError("Input must include 'finding', 'findings', or raw finding fields.")


def _kickoff_crew(crew: Crew, inputs: Dict[str, str]) -> None:
    crew.kickoff(inputs=inputs)


def process_single_finding(
    target: str,
    finding: Dict[str, Any],
    llm,
    *,
    index: int,
    section_prefix: str,
) -> ReportSection:
    finding_json = json.dumps(finding, ensure_ascii=False)

    analysis_agent = make_finding_analysis_agent(llm=llm)
    severity_agent = make_severity_agent(llm=llm)
    writer_agent = make_report_writer_agent(llm=llm)

    analysis_task = make_finding_analysis_task(analysis_agent)
    severity_task = make_severity_classification_task(severity_agent)
    report_task = make_report_writer_task(writer_agent)

    crew = Crew(
        agents=[analysis_agent, severity_agent, writer_agent],
        tasks=[analysis_task, severity_task, report_task],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )

    inputs = {"target": target, "finding": finding_json}
    endpoint = finding.get("endpoint", "unknown")
    logger.info("Running crew for finding %s (endpoint=%s)", index, endpoint)

    _kickoff_crew(crew, inputs)

    analysis = parse_task_output(analysis_task, FindingAnalysis)
    severity = parse_task_output(severity_task, SeverityClassification)
    section = parse_task_output(report_task, ReportSection)

    if not section.wstg:
        if severity.wstg_categories:
            section = section.model_copy(update={"wstg": severity.wstg_categories[0]})
        elif analysis.likely_wstg:
            section = section.model_copy(update={"wstg": analysis.likely_wstg})

    if not section.owasp and severity.owasp_categories:
        section = section.model_copy(update={"owasp": severity.owasp_categories[0]})

    if not section.cwe and severity.cwe_ids:
        section = section.model_copy(update={"cwe": ", ".join(severity.cwe_ids)})

    section = enrich_report_section(
        section,
        index,
        section_prefix=section_prefix,
        raw_finding=finding,
    )
    section.target = target

    logger.info(
        "Finding %s complete: %s [%s]",
        section.section_number,
        section.title,
        section.severity,
    )
    return section


def process_executive_summary(
    target: str,
    sections: List[ReportSection],
    llm,
) -> ExecutiveSummary:
    exec_agent = make_exec_summary_agent(llm=llm)
    exec_task = make_executive_summary_task(exec_agent)

    crew = Crew(
        agents=[exec_agent],
        tasks=[exec_task],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )

    report_sections_json = json.dumps(
        [s.model_dump() for s in sections],
        ensure_ascii=False,
    )
    _kickoff_crew(crew, {"target": target, "report_sections_json": report_sections_json})
    return parse_task_output(exec_task, ExecutiveSummary)


def generate_vapt_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    target, findings, section_prefix = normalize_input(payload)
    if not target:
        logger.warning("No target specified; using 'unknown_target'")
        target = "unknown_target"

    llm = get_llm(temperature=0.2)
    sections: List[ReportSection] = []

    total = len(findings)
    for index, finding in enumerate(findings, 1):
        logger.info("Processing finding %s/%s", index, total)
        section = process_single_finding(
            target,
            finding,
            llm,
            index=index,
            section_prefix=section_prefix,
        )
        sections.append(section)

    executive_summary: Optional[ExecutiveSummary] = None
    if len(sections) > 1:
        logger.info("Generating executive summary for %s findings", len(sections))
        executive_summary = process_executive_summary(target, sections, llm)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report_markdown = render_full_report(target, sections, executive_summary)

    docx_document = build_vapt_docx(
        target=target,
        sections=sections,
        generated_at=generated_at,
        executive_summary=executive_summary,
        section_prefix=section_prefix,
    )

    return {
        "target": target,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generated_at_display": generated_at,
        "findings_count": len(sections),
        "sections": [s.model_dump() for s in sections],
        "executive_summary": executive_summary.model_dump() if executive_summary else None,
        "report_markdown": report_markdown,
        "docx_document": docx_document,
    }


def generate_and_persist(payload: Dict[str, Any]) -> Dict[str, Any]:
    result = generate_vapt_report(payload)
    target = result["target"]

    structured = {
        "target": target,
        "generated_at_utc": result["generated_at_utc"],
        "findings_count": result["findings_count"],
        "sections": result["sections"],
        "executive_summary": result["executive_summary"],
    }

    json_path = save_findings_json(structured, target)
    docx_path = save_docx(result["docx_document"], target, suffix="vapt_report")
    md_path = save_markdown(result["report_markdown"], target)

    result["findings_json_path"] = json_path
    result["report_docx_path"] = docx_path
    result["report_markdown_path"] = md_path
    return result
