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
      "Write the final enterprise VAPT finding for target {target} using the project context, "
      "prior analysis, prior severity classification, and the raw tester evidence.\n\n"
      "Project Context (application/environment context only):\n{project_context}\n\n"
      "Raw finding JSON:\n{finding}\n\n"
      "Finding Analysis:\n{analysis}\n\n"
      "Severity Classification:\n{severity}\n\n"
      "Use project context to interpret the application context and tailor language or recommendations only when explicitly supported. "
      "Project context is not vulnerability evidence and does not prove vulnerability behavior, exploit success, architecture details, or business impact. "
      "Tester-provided evidence remains the source of truth. Use only explicit evidence, confirmed facts, and relevant retrieved RAG context. "
      "Separate Confirmed facts, AI inference, Recommendations, and Manual Verification requirements in the narrative. "
      "Do not treat technologies, authentication mechanisms, roles, assets, or notes as proof of a vulnerability. "
      "If a fact is missing or a classification is not supported, use N/A or 'Requires manual verification' rather than guessing.\n\n"
      "Produce: title, severity, OWASP, WSTG, CWE, description, business impact, "
      "affected_endpoints table rows, steps to reproduce, remediation, references. "
      "If no evidence exists, use N/A; if OWASP/CWE/WSTG cannot be confidently mapped, return 'Requires manual verification'.\n\n"
      "JSON_SCHEMA_HINT:\n" + JSON_SCHEMA_HINT.strip()
    ),
    expected_output=JSON_SCHEMA_HINT.strip(),
    agent=agent,
  )
