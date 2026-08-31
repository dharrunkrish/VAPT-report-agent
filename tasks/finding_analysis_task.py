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
            "Raw finding JSON:\n{finding}\n\n"
            "Extract technical context from observation, endpoint, and evidence. "
            "Use only explicit facts from the raw finding and any retrieved RAG context. "
            "Do not invent endpoints, payloads, exploit evidence, affected users, or vulnerability mappings. "
            "If evidence is missing, return N/A. If a classification cannot be confidently determined, "
            "return 'Requires manual verification'.\n\n"
            "JSON_SCHEMA_HINT:\n" + JSON_SCHEMA_HINT.strip()
        ),
        expected_output=JSON_SCHEMA_HINT.strip(),
        agent=agent,
    )
