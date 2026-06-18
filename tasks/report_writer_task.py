from crewai import Task

JSON_SCHEMA_HINT = """
Return ONLY a valid JSON object (no markdown fences) with these keys:
{{
  "target": "string",
  "finding_id": "string e.g. VAPT-001",
  "section_number": "string e.g. 5.1",
  "title": "string — concise vulnerability title",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFORMATIONAL",
  "cvss_score": 0.0,
  "cwe": "string e.g. CWE-639",
  "owasp": "string e.g. Broken Access Control (OWASP A01:2025)",
  "wstg": "string e.g. Testing for Privilege Escalation (WSTG-ATHZ-03)",
  "description": "string — full technical description paragraph(s)",
  "business_impact": "string",
  "affected_endpoints": [
    {{
      "endpoint": "string URL or path",
      "affected_roles": "string",
      "impact": "string",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW"
    }}
  ],
  "steps_to_reproduce": ["numbered step 1", "step 2"],
  "proof_of_concept": "string (sanitized)",
  "remediation": ["actionable recommendation 1"],
  "references": ["url or standard"]
}}
Map OWASP Top 10 2021/2025 and WSTG where applicable. Use professional enterprise VAPT language.
"""


def make_report_writer_task(agent) -> Task:
    return Task(
        description=(
            "Write the final enterprise VAPT finding for target {target} using all prior "
            "task outputs and this raw finding:\n{finding}\n\n"
            "Produce: title, severity, OWASP, WSTG, CWE, description, business impact, "
            "affected_endpoints table rows, steps to reproduce, remediation, references."
        ),
        expected_output=JSON_SCHEMA_HINT.strip(),
        agent=agent,
    )
