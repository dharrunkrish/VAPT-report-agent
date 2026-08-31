from typing import Any, Dict, List

from utils.schemas import ReportSection


def section_to_api_response(section: ReportSection) -> Dict[str, Any]:
    """Map internal ReportSection to frontend API contract."""
    technical_impact = (
        section.technical_description
        or section.description
        or section.proof_of_concept
        or ""
    )

    return {
        "title": section.title,
        "severity": section.severity or "Requires manual verification",
        "owasp": section.owasp or "Requires manual verification",
        "cwe": section.cwe or "Requires manual verification",
        "wstg": section.wstg or "Requires manual verification",
        "description": section.description or "N/A",
        "technical_impact": technical_impact or "N/A",
        "business_impact": section.business_impact or "N/A",
        "steps_to_reproduce": section.steps_to_reproduce or ["N/A"],
        "proof_of_concept": section.proof_of_concept or "N/A",
        "remediation": section.remediation_items() or ["N/A"],
        "references": section.references,
        "finding_id": section.finding_id,
        "section_number": section.section_number,
        "cvss_score": section.cvss_score,
        "affected_endpoints": [e.model_dump() for e in section.affected_endpoints],
    }
