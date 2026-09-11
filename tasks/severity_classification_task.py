from crewai import Task

JSON_SCHEMA_HINT = """
Return ONLY a valid JSON object (no markdown fences) with these keys:
{{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFORMATIONAL|Requires manual verification",
  "cvss_score": 0.0 or null,
  "cvss_vector": "string or null",
  "cwe_ids": ["CWE-XXX"],
  "owasp_categories": ["Broken Access Control (OWASP A01:2025)"],
  "wstg_categories": ["Testing for Privilege Escalation (WSTG-ATHZ-03)"],
  "justification": "string"
}}
Use the tester-confirmed evidence as the primary source of truth. Assign CVSS only when sufficient metrics are explicitly supported by evidence.
"""


def make_severity_classification_task(agent) -> Task:
    return Task(
        description=(
            "Classify severity for target {target} using the previous finding-analysis output and the raw evidence provided by the tester.\n\n"
            "Project Context (application context and environment context only):\n{project_context}\n\n"
            "Tester-confirmed raw finding evidence:\n{finding}\n\n"
            "AI Analysis (previous finding-analysis output):\n{analysis}\n\n"
            "AI Classification:\n"
            "- Treat project context as application/environment context only: target, scope, technologies, authentication, roles, assets, and notes.\n"
            "- Treat tester-provided evidence as the primary source of truth. Use endpoint, observation, evidence, request evidence, and affected roles as the basis for any claim.\n"
            "- Use project context to interpret relevance and tailor recommendations, but never treat project context itself as evidence of exploitation, attack success, or vulnerability existence.\n"
            "- Do not treat technologies, authentication mechanisms, roles, assets, scope entries, or notes as proof of a vulnerability.\n"
            "- Never invent attack success, exploitability, affected users, endpoints, payloads, security controls, CVSS metrics, CWE mappings, OWASP mappings, or WSTG mappings.\n"
            "- Authentication and roles may influence risk only when the actual evidence supports them.\n"
            "- Technologies may make recommendations more relevant, but they are not evidence that a vulnerability exists.\n"
            "- If the available evidence is insufficient to confidently classify severity, explicitly return severity='Requires manual verification', set cvss_score to null and cvss_vector to null, and explain why.\n"
            "- CVSS must only be assigned when sufficient metrics are supported by evidence. Preserve uncertainty rather than guessing.\n"
            "- Severity must be justified using observable evidence and relevant context.\n\n"
            "Manual Verification:\n"
            "If the evidence is incomplete, ambiguous, or unsupported, do not guess. Return 'Requires manual verification' instead.\n\n"
            "JSON_SCHEMA_HINT:\n" + JSON_SCHEMA_HINT.strip()
        ),
        expected_output=JSON_SCHEMA_HINT.strip(),
        agent=agent,
    )
