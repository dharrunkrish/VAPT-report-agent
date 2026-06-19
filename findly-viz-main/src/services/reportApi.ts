import type { Severity } from "@/store/findingsStore";
import { normalizeSeverity } from "@/lib/severity";

export interface FindingInput {
  id?: string | null;
  title?: string;
  severity?: Severity | string;
  owasp?: string;
  wstg?: string;
  endpoint?: string;
  observation?: string;
  evidence?: string;
  steps_to_reproduce?: string[];
  notes?: string;
  remediation?: string[];
  request_evidence?: string;
  affected_roles?: string;
}

export interface GenerateReportRequest {
  target: string;
  finding?: FindingInput;
  findings?: FindingInput[];
  section_prefix?: string;
}

export interface AffectedEndpoint {
  endpoint: string;
  affected_roles: string;
  impact: string;
  severity: string;
}

export interface GenerateReportResponse {
  title: string;
  severity: string;
  owasp: string;
  cwe: string;
  wstg?: string;
  description: string;
  technical_impact: string;
  business_impact: string;
  steps_to_reproduce: string[];
  proof_of_concept: string;
  remediation: string[];
  references: string[];
  finding_id?: string;
  section_number?: string;
  cvss_score?: number | null;
  affected_endpoints?: AffectedEndpoint[];
  markdown?: string;
  markdown_filename?: string | null;
  docx_filename?: string | null;
  json_filename?: string | null;
  findings_count?: number;
  executive_summary?: string | null;
}

export class ReportApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ReportApiError";
    this.status = status;
  }
}

const API_BASE = import.meta.env.VITE_VAPT_API_URL ?? "http://localhost:8000";

async function parseErrorResponse(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) {
      return data.detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join("; ");
    }
    return JSON.stringify(data);
  } catch {
    return response.statusText || "Request failed";
  }
}

export async function generateReport(
  payload: GenerateReportRequest,
): Promise<GenerateReportResponse> {
  const findings =
    payload.findings ??
    (payload.finding ? [payload.finding] : []);

  const body = {
    target: payload.target,
    findings,
    section_prefix: payload.section_prefix,
  };

  const response = await fetch(`${API_BASE}/generate-report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const message = await parseErrorResponse(response);
    throw new ReportApiError(message, response.status);
  }

  return response.json();
}

export interface GenerateFullReportRequest {
  target: string;
  findings: FindingInput[];
  section_prefix?: string;
}

export interface GenerateFullReportResponse extends GenerateReportResponse {}

export async function generateFullReport(
  payload: GenerateFullReportRequest,
): Promise<GenerateFullReportResponse> {
  return generateReport(payload);
}

export async function downloadReportFile(
  filename: string,
  downloadAs: string,
): Promise<void> {
  const response = await fetch(`${API_BASE}/files/${encodeURIComponent(filename)}`);
  if (!response.ok) {
    throw new ReportApiError("Failed to download file", response.status);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = downloadAs;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

export function getApiBaseUrl(): string {
  return API_BASE;
}

export function reportToMarkdownText(report: GenerateReportResponse): string {
  const steps = report.steps_to_reproduce
    .map((s, i) => `${i + 1}. ${s}`)
    .join("\n");
  const remediation = report.remediation.map((r) => `- ${r}`).join("\n");
  const refs =
    report.references.length > 0
      ? `\n## References\n${report.references.map((r) => `- ${r}`).join("\n")}`
      : "";

  return `# ${report.title}

**Severity:** ${report.severity}
**OWASP:** ${report.owasp}
**CWE:** ${report.cwe}
**WSTG:** ${report.wstg ?? "N/A"}

## Description
${report.description}

## Technical Impact
${report.technical_impact}

## Business Impact
${report.business_impact}

## Steps to Reproduce
${steps}

## Proof of Concept
\`\`\`
${report.proof_of_concept}
\`\`\`

## Remediation
${remediation}${refs}
`;
}

export function findingsToPreviewMarkdown(
  target: string,
  findings: FindingInput[],
): string {
  return findings
    .map((f, i) => {
      const steps = (f.steps_to_reproduce ?? [])
        .map((s, j) => `${j + 1}. ${s}`)
        .join("\n");
      const remediation = (f.remediation ?? []).map((r) => `- ${r}`).join("\n");
      return `## ${i + 1}. ${f.title ?? "Untitled"} (${f.severity ?? "MEDIUM"})

**Target:** ${target}
**ID:** ${f.id ?? "N/A"}
**OWASP:** ${f.owasp ?? "N/A"}
**WSTG:** ${f.wstg ?? "N/A"}
**Endpoint:** ${f.endpoint ?? "N/A"}

### Observation
${f.observation ?? ""}

### Evidence
${f.evidence ?? ""}

### Steps to Reproduce
${steps || "N/A"}

### Notes
${f.notes ?? ""}

### Remediation
${remediation || "N/A"}

### Request Evidence
\`\`\`http
${f.request_evidence ?? ""}
\`\`\`
`;
    })
    .join("\n---\n\n");
}
