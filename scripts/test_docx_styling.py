#!/usr/bin/env python3
"""Generate a sample .docx without calling the LLM (styling smoke test)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.docx_report import build_vapt_docx
from utils.output import save_docx
from utils.schemas import AffectedEndpoint, ReportSection

sections = [
    ReportSection(
        finding_id="VAPT-001",
        section_number="5.1",
        title="Vertical Privilege Escalation in User Management Module",
        severity="CRITICAL",
        owasp="Broken Access Control (OWASP A01:2025)",
        wstg="Testing for Privilege Escalation (WSTG-ATHZ-03)",
        cwe="CWE-269",
        description=(
            "A low-privileged authenticated user can invoke administrative user-management "
            "functions by manipulating request parameters, resulting in unauthorized privilege escalation."
        ),
        affected_endpoints=[
            AffectedEndpoint(
                endpoint="/api/admin/users",
                affected_roles="Standard authenticated users",
                impact="Full administrative control over user accounts",
                severity="CRITICAL",
            ),
            AffectedEndpoint(
                endpoint="/api/admin/roles",
                affected_roles="Standard authenticated users",
                impact="Role assignment modification",
                severity="HIGH",
            ),
        ],
        steps_to_reproduce=[
            "Authenticate as a low-privileged user.",
            "Send a POST request to /api/admin/users with elevated role parameters.",
            "Observe successful creation of administrative accounts.",
        ],
        remediation=[
            "Enforce server-side role-based access control on all administrative endpoints.",
            "Implement authorization checks using policy engines tied to user identity.",
            "Log and alert on privilege escalation attempts.",
        ],
    )
]

doc = build_vapt_docx(
    target="example.com",
    sections=sections,
    generated_at="2026-05-28 18:00:00 UTC",
)
path = save_docx(doc, "example", suffix="vapt_report")
print(f"Sample report written to: {path}")
