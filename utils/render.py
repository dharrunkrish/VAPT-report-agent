from datetime import datetime, timezone
from typing import List, Optional

from utils.schemas import ExecutiveSummary, ReportSection


def _bullet_list(items: List[str]) -> str:
    if not items:
        return "_None provided._\n"
    return "\n".join(f"- {item}" for item in items) + "\n"


def render_finding_section(section: ReportSection, index: int) -> str:
    cvss = f"{section.cvss_score:.1f}" if section.cvss_score is not None else "N/A"
    cwe = section.cwe or "N/A"
    owasp = section.owasp or "N/A"
    wstg = section.wstg or "N/A"
    finding_id = section.finding_id or f"VAPT-{index:03d}"
    section_num = section.section_number or str(index)
    description = section.description or section.technical_description or ""
    steps = "\n".join(f"{i}. {step}" for i, step in enumerate(section.steps_to_reproduce, 1))

    endpoints_md = ""
    if section.affected_endpoints:
        rows = "\n".join(
            f"| {e.endpoint} | {e.affected_roles} | {e.impact} | {e.severity} |"
            for e in section.affected_endpoints
        )
        endpoints_md = (
            "\n### Affected Endpoints\n"
            "| Endpoint | Affected Roles | Impact | Severity |\n"
            "|----------|----------------|--------|----------|\n"
            f"{rows}\n"
        )

    poc_md = ""
    if section.proof_of_concept:
        poc_md = f"\n### Proof of Concept\n```\n{section.proof_of_concept.strip()}\n```\n"

    refs = ""
    if section.references:
        refs = "\n### References\n" + _bullet_list(section.references)

    return f"""## {section_num} {section.title}

| Field | Value |
|-------|-------|
| **ID** | {finding_id} |
| **Severity** | {section.severity} |
| **CVSS v3.1** | {cvss} |
| **OWASP** | {owasp} |
| **WSTG** | {wstg} |
| **CWE** | {cwe} |

### Description
{description}
{endpoints_md}
### Steps to Reproduce
{steps}
{poc_md}
### Remediation
{_bullet_list(section.remediation_items())}{refs}
---
"""


def render_executive_summary(summary: ExecutiveSummary) -> str:
    findings_table = ""
    if summary.key_findings:
        rows = "\n".join(
            f"| {f.title} | {f.severity} | {f.short_impact} |"
            for f in summary.key_findings
        )
        findings_table = (
            "\n| Finding | Severity | Impact |\n|---------|----------|--------|\n"
            + rows
            + "\n"
        )

    priorities = _bullet_list(summary.remediation_priorities)

    return f"""## Executive Summary

**Overall risk level:** {summary.overall_risk_level}

{summary.executive_summary.strip()}

### Key Findings
{findings_table if findings_table else "_No key findings listed._\n"}

### Remediation Priorities
{priorities}
---
"""


def render_full_report(
    target: str,
    sections: List[ReportSection],
    executive_summary: Optional[ExecutiveSummary] = None,
) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    header = f"""# Vulnerability Assessment & Penetration Testing Report

**Target:** {target}
**Report generated:** {generated}
**Classification:** Confidential — Internal Use

---

"""

    body_parts = []
    if executive_summary:
        body_parts.append(render_executive_summary(executive_summary))

    for idx, section in enumerate(sections, 1):
        body_parts.append(render_finding_section(section, idx))

    return header + "\n".join(body_parts)
