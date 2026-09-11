from crewai import Task

JSON_SCHEMA_HINT = """
Return ONLY a valid JSON object (no markdown fences) with these keys:
{{
  "vulnerability_title": "string",
  "vulnerability_type": "string",
  "affected_components": ["string"],
  "attack_vector": "string",
  "evidence_summary": "string",
  "technical_description": "string",
  "likely_cwe": "string or null",
  "likely_owasp": "string or null",
  "likely_wstg": "string or null",
  "assumptions": ["string"]
}}
"""


def make_finding_analysis_task(agent) -> Task:
    return Task(
        description=(
            "Analyze the security finding for target: {target}\n\n"
            "Project Context (environment/application context only):\n{project_context}\n\n"
            "Raw finding JSON:\n{finding}\n\n"
            "Treat the project context as environmental context only. It may describe the target, scope, "
            "technologies, authentication mechanisms, roles, assets, and notes. It is not vulnerability evidence. "
            "The tester-confirmed raw finding evidence remains the primary source of truth for any claim about the vulnerability. "
            "Never treat a technology, authentication mechanism, role, asset, scope entry, or project note as proof that a vulnerability exists. "
            "Do not invent endpoints, payloads, exploit evidence, affected users, security controls, or vulnerability evidence. "
            "Use project context only to interpret the supplied finding. Extract technical context from observation, endpoint, and evidence. "
            "If evidence is missing, return N/A. If a classification cannot be confidently determined, "
            "return 'Requires manual verification'.\n\n"
            "JSON_SCHEMA_HINT:\n" + JSON_SCHEMA_HINT.strip()
        ),
        expected_output=JSON_SCHEMA_HINT.strip(),
        agent=agent,
    )
