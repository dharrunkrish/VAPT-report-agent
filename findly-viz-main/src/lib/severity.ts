import type { Severity } from "@/store/findingsStore";

export const SEVERITY_OPTIONS: Severity[] = [
  "CRITICAL",
  "HIGH",
  "MEDIUM",
  "LOW",
  "INFO",
];

export function normalizeSeverity(value?: string): Severity {
  const upper = (value ?? "MEDIUM").toUpperCase();
  if (SEVERITY_OPTIONS.includes(upper as Severity)) return upper as Severity;
  if (upper.includes("CRITICAL")) return "CRITICAL";
  if (upper.includes("HIGH")) return "HIGH";
  if (upper.includes("LOW")) return "LOW";
  if (upper.includes("INFO")) return "INFO";
  return "MEDIUM";
}

export function severityBadgeClass(severity: Severity | string): string {
  switch (normalizeSeverity(severity)) {
    case "CRITICAL":
      return "bg-red-600 text-white border-red-700";
    case "HIGH":
      return "bg-orange-500 text-white border-orange-600";
    case "MEDIUM":
      return "bg-yellow-500 text-black border-yellow-600";
    case "LOW":
      return "bg-blue-500 text-white border-blue-600";
    case "INFO":
    default:
      return "bg-gray-400 text-white border-gray-500";
  }
}

export function countBySeverity(findings: { severity: Severity | string }[]) {
  const counts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFO: 0 };
  for (const f of findings) {
    const key = normalizeSeverity(f.severity);
    counts[key] += 1;
  }
  return counts;
}
