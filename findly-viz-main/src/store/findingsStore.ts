import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";

export interface Finding {
  id?: string;
  title: string;
  severity: Severity;
  owasp?: string;
  wstg?: string;
  endpoint?: string;
  observation?: string;
  evidence?: string;
  steps_to_reproduce?: string[];
  notes?: string;
  remediation?: string[];
  request_evidence?: string;
}

interface FindingsStore {
  target: string;
  findings: Finding[];
  setTarget: (t: string) => void;
  addFinding: (f: Finding) => void;
  updateFinding: (index: number, f: Finding) => void;
  removeFinding: (index: number) => void;
  reorderFindings: (from: number, to: number) => void;
  clearAll: () => void;
  importFindings: (target: string, findings: Finding[]) => void;
}

export const useFindingsStore = create<FindingsStore>()(
  persist(
    (set) => ({
      target: "",
      findings: [],
      setTarget: (t) => set({ target: t }),
      addFinding: (f) => set((s) => ({ findings: [...s.findings, f] })),
      updateFinding: (i, f) =>
        set((s) => {
          const findings = [...s.findings];
          findings[i] = f;
          return { findings };
        }),
      removeFinding: (i) =>
        set((s) => ({
          findings: s.findings.filter((_, idx) => idx !== i),
        })),
      reorderFindings: (from, to) =>
        set((s) => {
          const findings = [...s.findings];
          const [moved] = findings.splice(from, 1);
          findings.splice(to, 0, moved);
          return { findings };
        }),
      clearAll: () => set({ findings: [], target: "" }),
      importFindings: (target, findings) => set({ target, findings }),
    }),
    { name: "vapt-findings-store-v1" },
  ),
);

export function emptyFinding(): Finding {
  return {
    title: "",
    severity: "MEDIUM",
    owasp: "",
    wstg: "",
    endpoint: "",
    observation: "",
    evidence: "",
    steps_to_reproduce: [""],
    notes: "",
    remediation: [""],
    request_evidence: "",
  };
}

export const SAMPLE_FINDING: Finding = {
  id: "XPCON-2026-027",
  title: "Parameter Tampering: Educator Can Access Unauthorized Classes",
  severity: "HIGH",
  owasp: "Broken Access Control (OWASP A01:2025)",
  wstg: "WSTG-ATHZ-02",
  endpoint: "GET /ulapi/classes?page=1&per_page=10&order_by=section_name",
  observation:
    "Removing show_only_my_classes=true parameter returns all classes including unauthorized ones",
  evidence:
    "Educator can rename, delete, assign elements on unauthorized classes via UI or API",
  steps_to_reproduce: [
    "Login as an Educator user",
    "Navigate to My Classes",
    "Intercept the request using Burp Suite",
    "Remove the show_only_my_classes=true parameter",
    "Forward the request",
    "Observe all classes including unassigned ones are returned",
    "Perform operations on unauthorized classes via UI or API",
  ],
  notes:
    "Backend does not validate class ownership. Frontend-only restriction is bypassable.",
  remediation: [
    "Enforce server-side authorization checks on every class operation",
    "Validate class ownership against the authenticated user on the backend",
    "Remove reliance on frontend parameters for access control",
    "Implement role-based access control at the API layer",
  ],
  request_evidence:
    "GET /ulapi/classes?page=1&per_page=10&order_by=section_name HTTP/1.1\nHost: example.com\nAuthorization: Bearer <educator_token>",
};

export const SAMPLE_TARGET = "example.com";
