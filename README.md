# VAPTagen — AI-assisted VAPT Report Generator

Transforms structured penetration-test findings into **enterprise Microsoft Word (.docx)** reports, plus JSON and Markdown exports. Uses **CrewAI** + **Groq**.

## Features

- Professional **Word (.docx)** output (Calibri 11, styled tables, severity colors)
- Metadata table: ID, Severity, OWASP, WSTG
- Affected endpoints table with role/impact/severity columns
- Numbered reproduction steps and bullet remediation
- Automatic section numbering (`5.1`, `5.2`, …)
- JSON findings export + Markdown (secondary)
- Executive summary for multi-finding inputs

## Setup

```bash
cd VAPTagen
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set GROQ_API_KEY in .env
```

**Python 3.12:** requires `setuptools==69.5.1` (see `requirements.txt`) for CrewAI `pkg_resources`.

## Run

```bash
python3 main.py --input inputs/example_single_finding.json
python3 main.py --input inputs/example_multiple_findings.json
```

## Output files

| File | Example |
|------|---------|
| Word report | `outputs/example.com_vapt_report_20260528_180249.docx` |
| JSON findings | `outputs/example.com_findings_20260528_180249.json` |
| Markdown | `outputs/example.com_report_20260528_180249.md` |

## Styling smoke test (no LLM)

```bash
python3 scripts/test_docx_styling.py
# → outputs/example_vapt_report_<timestamp>.docx
```

## Input format

```json
{
  "target": "example.com",
  "section_prefix": "5",
  "findings": [
    {
      "observation": "Changing user ID exposes another user's data.",
      "endpoint": "/api/user/123",
      "evidence": "IDOR confirmed by modifying identifiers."
    }
  ]
}
```

Single finding: use `"finding": { ... }` instead of `"findings"`.

## Word report styling

| Element | Style |
|---------|--------|
| Font | Calibri 11 |
| Section heading | `5.1 Title` — bold |
| Metadata labels | Dark purple column, white text |
| Severity CRITICAL | Red background, white text |
| Table headers | Navy blue, white text |
| Description | Justified body text |
| Steps | Numbered list |
| Remediation | Bullet list |

## Architecture

```
main.py / api_server.py → crew_orchestrator.py
              ├── CrewAI agents (analysis → severity → writer)
              ├── utils/docx_report.py  → .docx
              ├── utils/output.py       → JSON
              └── utils/render.py       → Markdown

findly-viz-main/ (frontend)
  └── POST /generate-report → api_server.py
```
