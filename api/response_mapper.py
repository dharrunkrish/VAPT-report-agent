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
        "severity": section.severity,
        "owasp": section.owasp or "",
        "cwe": section.cwe or "",
        "wstg": section.wstg or "",
        "description": section.description or "",
        "technical_impact": technical_impact,
        "business_impact": section.business_impact or "",
        "steps_to_reproduce": section.steps_to_reproduce,
        "proof_of_concept": section.proof_of_concept or "",
        "remediation": section.remediation_items(),
        "references": section.references,
        "finding_id": section.finding_id,
        "section_number": section.section_number,
        "cvss_score": section.cvss_score,
        "affected_endpoints": [e.model_dump() for e in section.affected_endpoints],
    }
