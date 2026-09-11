from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProjectFinding(BaseModel):
    """
    A security finding associated with a VAPT project.

    Tester-provided evidence remains the source of truth. AI-generated values and
    reviewer confirmation state are stored separately so they can be audited and
    distinguished from approved/overridden values.
    """

    model_config = ConfigDict(extra="forbid")

    finding_id: str
    project_id: str

    endpoint: str = ""
    observation: str = ""
    evidence: str = ""

    notes: Optional[str] = None
    request_evidence: Optional[str] = None
    affected_roles: Optional[str] = None

    status: str = "open"
    review_status: Literal["unreviewed", "reviewed", "approved", "overridden"] = "unreviewed"

    ai_analysis: Optional[str] = None
    ai_severity: Optional[str] = None
    ai_remediation: List[str] = Field(default_factory=list)

    confirmed_severity: Optional[str] = None
    confirmed_remediation: List[str] = Field(default_factory=list)
    review_notes: Optional[str] = None

    version: int = 1

    @model_validator(mode="after")
    def validate_review_state(self):
        if self.review_status == "unreviewed":
            if self.confirmed_severity is not None or self.confirmed_remediation:
                raise ValueError(
                    "Unreviewed findings must not contain confirmed severity or remediation values."
                )

        if self.review_status == "approved":
            if (
                self.ai_severity is not None
                and self.confirmed_severity is not None
                and self.confirmed_severity != self.ai_severity
            ):
                raise ValueError(
                    "Approved severity must match the original AI recommendation when AI severity exists."
                )
            if (
                self.ai_remediation
                and self.confirmed_remediation
                and self.confirmed_remediation != self.ai_remediation
            ):
                raise ValueError(
                    "Approved remediation must match the original AI recommendation when AI remediation exists."
                )

        if self.review_status == "overridden":
            if (
                self.ai_severity is not None
                and self.confirmed_severity is not None
                and self.confirmed_severity == self.ai_severity
                and not self.confirmed_remediation
            ):
                raise ValueError(
                    "Override state requires a reviewer-approved change from the AI recommendation."
                )

        return self
