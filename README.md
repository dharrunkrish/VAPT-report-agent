# VAPTagen — AI-Assisted VAPT Report Generator

VAPTagen transforms structured penetration testing findings into professional VAPT reports using **CrewAI**, **Groq**, and a modern web interface.

The platform supports:

* AI-assisted vulnerability analysis
* Structured finding generation
* Enterprise-grade Microsoft Word (.docx) reports
* JSON and Markdown exports
* FastAPI backend
* React/TanStack frontend

---

# Features

## Report Generation

* Professional Microsoft Word (.docx) reports
* JSON findings export
* Markdown export
* Automatic section numbering (`5.1`, `5.2`, ...)
* Executive summary generation
* Multi-stage AI analysis pipeline

## Report Formatting

* Calibri 11 font
* Severity-based color coding
* Styled metadata tables
* Affected endpoints table
* Numbered reproduction steps
* Bullet remediation recommendations
* Executive summary support

## AI Pipeline

CrewAI workflow:

```text
Finding Analysis
        ↓
Severity Classification
        ↓
Report Writing
        ↓
DOCX / JSON / Markdown Generation
```

---

# Architecture

```text
Frontend (React + TanStack)
        ↓
POST /generate-report
        ↓
FastAPI Backend
        ↓
CrewAI Orchestrator
        ↓
Groq LLM
        ↓
Report Generation
        ↓
DOCX / JSON / Markdown
```

```text
main.py
api_server.py
crew_orchestrator.py
│
├── agents/
│   ├── finding_analysis.py
│   ├── severity.py
│   ├── report_writer.py
│   └── exec_summary.py
│
├── utils/
│   ├── docx_report.py
│   ├── output.py
│   ├── render.py
│   └── schemas.py
│
└── findly-viz-main/
    └── Frontend Application
```

---

# Prerequisites

* Python 3.12+
* Node.js 20+
* npm
* Groq API Key

---

# Backend Setup

```bash
cd ~/VAPTagen

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Create environment file:

```bash
cp .env.example .env
```

Update:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
OUTPUT_DIR=outputs
LOG_LEVEL=INFO
```

---

# Start Backend

```bash
cd ~/VAPTagen

source .venv/bin/activate

uvicorn api_server:app --reload --log-level debug
```

Backend runs on:

```text
http://localhost:8000
```

API Documentation:

```text
http://localhost:8000/docs
```

OpenAPI Schema:

```text
http://localhost:8000/openapi.json
```

---

# Frontend Setup

```bash
cd ~/VAPTagen/findly-viz-main

cp .env.example .env

npm install
```

---

# Start Frontend

```bash
cd ~/VAPTagen/findly-viz-main

npm run dev
```

Frontend runs on:

```text
http://localhost:5173
```

---

# API Endpoints

## Health Check

```http
GET /health
```

## Generate Report

```http
POST /generate-report
```

## Download Generated Files

```http
GET /files/{filename}
```

---

# Example Input

## JSON Format

```json
{
  "target": "example.com",
  "finding": {
    "id": "XPCON-2026-027",
    "title": "Parameter Tampering: Educator Can Access Unauthorized Classes",
    "severity": "HIGH",
    "owasp": "Broken Access Control (OWASP A01:2025)",
    "wstg": "WSTG-ATHZ-02",
    "endpoint": "GET /ulapi/classes?page=1&per_page=10",
    "observation": "Removing show_only_my_classes=true returns all classes",
    "evidence": "Educator can rename, delete, assign elements on unauthorized classes",
    "request_evidence": "GET /ulapi/classes HTTP/1.1"
  }
}
```

---

# CLI Usage

Generate reports directly without the frontend:

```bash
python3 main.py --input inputs/example_single_finding.json
```

Multiple findings:

```bash
python3 main.py --input inputs/example_multiple_findings.json
```

---

# Output Files

| File Type       | Example                                              |
| --------------- | ---------------------------------------------------- |
| DOCX Report     | outputs/example.com_vapt_report_20260617_115248.docx |
| JSON Findings   | outputs/example.com_findings_20260617_115248.json    |
| Markdown Report | outputs/example.com_report_20260617_115248.md        |

---

# DOCX Styling Test

Run styling validation without calling the LLM:

```bash
python3 scripts/test_docx_styling.py
```

Output:

```text
outputs/example_vapt_report_<timestamp>.docx
```

---

# Word Report Styling

| Element            | Style             |
| ------------------ | ----------------- |
| Font               | Calibri 11        |
| Section Heading    | Bold              |
| Metadata Labels    | Dark Purple       |
| Critical Severity  | Red Background    |
| High Severity      | Orange Background |
| Table Headers      | Navy Blue         |
| Description        | Justified         |
| Reproduction Steps | Numbered          |
| Remediation        | Bullet List       |

---

# Current Workflow

```text
User Finding
      ↓
Chat Assistant
      ↓
Structured Finding Preview
      ↓
Transfer to Report
      ↓
POST /generate-report
      ↓
CrewAI Processing
      ↓
DOCX / JSON / Markdown Output
```
