import type { Finding } from "@/store/findingsStore";
import { normalizeSeverity } from "@/lib/severity";

export interface ParsedFindingsPayload {
  target: string;
  findings: Finding[];
}

function normalizeFinding(raw: Record<string, unknown>): Finding {
  const steps = raw.steps_to_reproduce;
  const remediation = raw.remediation;

  return {
    id: typeof raw.id === "string" ? raw.id : undefined,
    title: typeof raw.title === "string" ? raw.title : "Untitled Finding",
    severity: normalizeSeverity(typeof raw.severity === "string" ? raw.severity : "MEDIUM"),
    owasp: typeof raw.owasp === "string" ? raw.owasp : "",
    wstg: typeof raw.wstg === "string" ? raw.wstg : "",
    endpoint: typeof raw.endpoint === "string" ? raw.endpoint : "",
    observation: typeof raw.observation === "string" ? raw.observation : "",
    evidence: typeof raw.evidence === "string" ? raw.evidence : "",
    steps_to_reproduce: Array.isArray(steps)
      ? steps.map(String).filter(Boolean)
      : [""],
    notes: typeof raw.notes === "string" ? raw.notes : "",
    remediation: Array.isArray(remediation)
      ? remediation.map(String).filter(Boolean)
      : [""],
    request_evidence:
      typeof raw.request_evidence === "string" ? raw.request_evidence : "",
  };
}

export function parseFindingsJson(data: unknown): ParsedFindingsPayload {
  if (!data || typeof data !== "object") {
    throw new Error("Invalid JSON: expected an object");
  }

  const obj = data as Record<string, unknown>;
  const target = typeof obj.target === "string" ? obj.target : "";

  if (obj.finding && typeof obj.finding === "object") {
    return {
      target,
      findings: [normalizeFinding(obj.finding as Record<string, unknown>)],
    };
  }

  if (Array.isArray(obj.findings)) {
    if (obj.findings.length === 0) {
      throw new Error("findings array is empty");
    }
    return {
      target,
      findings: obj.findings.map((f, i) => {
        if (!f || typeof f !== "object") {
          throw new Error(`Finding #${i + 1} must be an object`);
        }
        return normalizeFinding(f as Record<string, unknown>);
      }),
    };
  }

  throw new Error('JSON must include "finding" or "findings"');
}

export function findingToApiPayload(finding: Finding) {
  return {
    id: finding.id || null,
    title: finding.title,
    severity: finding.severity,
    owasp: finding.owasp || "",
    wstg: finding.wstg || "",
    endpoint: finding.endpoint || "",
    observation: finding.observation || "",
    evidence: finding.evidence || "",
    steps_to_reproduce: (finding.steps_to_reproduce ?? []).filter(Boolean),
    notes: finding.notes || "",
    remediation: (finding.remediation ?? []).filter(Boolean),
    request_evidence: finding.request_evidence || "",
  };
}
