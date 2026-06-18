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
            "Do not invent data that was not supplied."
        ),
        expected_output=JSON_SCHEMA_HINT.strip(),
        agent=agent,
    )
