from crewai import Task

JSON_SCHEMA_HINT = """
Return ONLY a valid JSON object (no markdown fences) with these keys:
{{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFORMATIONAL",
  "cvss_score": 0.0,
  "cvss_vector": "string or null",
  "cwe_ids": ["CWE-XXX"],
  "owasp_categories": ["Broken Access Control (OWASP A01:2025)"],
  "wstg_categories": ["Testing for Privilege Escalation (WSTG-ATHZ-03)"],
  "justification": "string"
}}
Use prior analysis context. Assign CVSS only when sufficient information exists.
"""


def make_severity_classification_task(agent) -> Task:
    return Task(
        description=(
            "Using the finding analysis from the previous task and raw finding for "
            "target {target}, classify severity and map to OWASP and WSTG.\n\n"
            "Raw finding JSON:\n{finding}"
        ),
        expected_output=JSON_SCHEMA_HINT.strip(),
        agent=agent,
    )
