from crewai import Task

JSON_SCHEMA_HINT = """
Return ONLY a valid JSON object (no markdown fences) with these keys:
{{
  "target": "string",
  "overall_risk_level": "Critical|High|Medium|Low",
  "key_findings": [
    {{"title": "string", "severity": "string", "short_impact": "string"}}
  ],
  "remediation_priorities": ["priority 1"],
  "executive_summary": "markdown text for management audience"
}}
"""


def make_executive_summary_task(agent) -> Task:
    return Task(
        description=(
            "Create an executive summary for target: {target}\n\n"
            "All finding report sections (JSON array):\n{report_sections_json}\n\n"
            "Summarize risk posture, highlight critical issues, and list remediation priorities."
        ),
        expected_output=JSON_SCHEMA_HINT.strip(),
        agent=agent,
    )
