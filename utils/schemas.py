# NOTE: Do not use `from __future__ import annotations` here.
# CrewAI 0.86 schema introspection breaks on stringified annotations.

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FindingAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vulnerability_title: Optional[str] = None
    vulnerability_type: Optional[str] = None
    affected_components: List[str] = Field(default_factory=list)
    attack_vector: Optional[str] = None
    evidence_summary: Optional[str] = None
    technical_description: Optional[str] = None
    likely_cwe: Optional[str] = None
    likely_owasp: Optional[str] = None
    likely_wstg: Optional[str] = None
    assumptions: List[str] = Field(default_factory=list)


class SeverityClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: str
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    cwe_ids: List[str] = Field(default_factory=list)
    owasp_categories: List[str] = Field(default_factory=list)
    wstg_categories: List[str] = Field(default_factory=list)
    justification: Optional[str] = None


class AffectedEndpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    endpoint: str
    affected_roles: str = Field(
        default="Authenticated low-privileged users",
        description="Roles that can exploit or are affected.",
    )
    impact: str
    severity: str


class ReportSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: Optional[str] = None
    section_number: Optional[str] = None
    target: Optional[str] = None
    title: str
    severity: str
    cvss_score: Optional[float] = None
    cwe: Optional[str] = None
    owasp: Optional[str] = None
    wstg: Optional[str] = None
    description: str = ""
    technical_description: Optional[str] = None
    business_impact: Optional[str] = None
    affected_endpoints: List[AffectedEndpoint] = Field(default_factory=list)
    steps_to_reproduce: List[str] = Field(default_factory=list)
    proof_of_concept: Optional[str] = None
    remediation: List[str] = Field(default_factory=list)
    remediation_recommendations: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if not data.get("description") and data.get("technical_description"):
            data["description"] = data["technical_description"]
        if not data.get("remediation") and data.get("remediation_recommendations"):
            data["remediation"] = data["remediation_recommendations"]
        return data

    def remediation_items(self) -> List[str]:
        return self.remediation or self.remediation_recommendations or []


class KeyFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    severity: str
    short_impact: str


class ExecutiveSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target: Optional[str] = None
    overall_risk_level: str
    key_findings: List[KeyFinding] = Field(default_factory=list)
    remediation_priorities: List[str]
    executive_summary: str


def enrich_report_section(
    section: ReportSection,
    index: int,
    *,
    section_prefix: str = "5",
    raw_finding: Optional[Dict[str, Any]] = None,
) -> ReportSection:
    """Assign IDs, section numbers, and default affected-endpoint rows when missing."""
    data = section.model_dump()

    if not data.get("finding_id"):
        data["finding_id"] = f"VAPT-{index:03d}"
    if not data.get("section_number"):
        data["section_number"] = f"{section_prefix}.{index}"

    if not data.get("affected_endpoints") and raw_finding:
        endpoint = raw_finding.get("endpoint", "N/A")
        roles = raw_finding.get("affected_roles", "Authenticated low-privileged users")
        impact = section.business_impact or section.description[:200] if section.description else "See description"
        data["affected_endpoints"] = [
            {
                "endpoint": endpoint,
                "affected_roles": roles,
                "impact": impact[:300],
                "severity": section.severity.upper(),
            }
        ]

    return ReportSection.model_validate(data)
