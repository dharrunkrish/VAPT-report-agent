# Frontend ↔ Backend Integration

The frontend lives in `findly-viz-main/` (Lovable/TanStack Start UI).
The backend API is the VAPTagen FastAPI server.

## 1. Start the backend API

```bash
cd VAPTagen
source .venv/bin/activate
pip install -r requirements.txt
# Ensure .env has GROQ_API_KEY
python3 api_server.py
# → http://localhost:8000
```

## 2. Configure the frontend

```bash
cd findly-viz-main
cp .env.example .env
# VITE_VAPT_API_URL=http://localhost:8000
npm install
npm run dev
```

## 3. Use the app

| Route | Purpose |
|-------|---------|
| `/` | Existing chat-style VAPT assistant |
| `/report` | Structured form → AI report generation |

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/generate-report` | Generate VAPT finding |
| GET | `/files/{filename}` | Download DOCX / Markdown / JSON |

### Request (POST /generate-report)

```json
{
  "target": "example.com",
  "finding": {
    "endpoint": "/api/user/123",
    "observation": "...",
    "evidence": "...",
    "notes": "...",
    "request_evidence": "POST /auth/..."
  }
}
```

### Response

Returns title, severity, OWASP, CWE, description, impacts, steps, PoC, remediation, references, plus `markdown`, `docx_filename`, etc.

## Frontend files added

```
src/services/reportApi.ts      — API client + types
src/hooks/useGenerateReport.ts — loading/error/state + localStorage
src/components/ReportViewer.tsx — report display + copy/download
src/pages/ReportGenerator.tsx   — input form + workflow
src/routes/report.tsx           — /report route
```

## CORS

Backend allows `http://localhost:5173` and `http://localhost:8080` by default.
Override with `CORS_ORIGINS` in VAPTagen `.env`.
