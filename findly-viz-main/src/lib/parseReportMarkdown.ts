import { normalizeSeverity } from "@/lib/severity";
import type { Finding } from "@/store/findingsStore";

function pick(markdown: string, patterns: RegExp[]): string {
  for (const pattern of patterns) {
    const match = markdown.match(pattern);
    if (match?.[1]?.trim()) return match[1].trim();
  }
  return "";
}

function pickList(markdown: string, sectionPattern: RegExp): string[] {
  const match = markdown.match(sectionPattern);
  if (!match?.[1]) return [""];
  const lines = match[1]
    .split("\n")
    .map((l) => l.replace(/^\d+\.\s*/, "").trim())
    .filter(Boolean);
  return lines.length > 0 ? lines : [""];
}

function pickCodeBlock(markdown: string): string {
  const httpBlock = markdown.match(
    /### 💻 Technical Proof of Concept[\s\S]*?```(?:http)?\n([\s\S]*?)```/i,
  );
  if (httpBlock?.[1]) return httpBlock[1].trim();

  const anyBlock = markdown.match(/```(?:http)?\n([\s\S]*?)```/);
  return anyBlock?.[1]?.trim() ?? "";
}

function pickSeverity(markdown: string): Finding["severity"] {
  const raw = pick(markdown, [
    /\*\*Severity\*\*\s*\|\s*(?:🔴|🟠|🟡|🔵|⚪)?\s*([A-Z]+)/i,
    /Severity[:\s]+([A-Z]+)/i,
  ]);
  return normalizeSeverity(raw || "MEDIUM");
}

export function parseReportMarkdown(markdown: string): { target: string; finding: Finding } {
  const target = pick(markdown, [
    /\|\s*\*\*Target\*\*\s*\|\s*`([^`]+)`/i,
    /Target Information[\s\S]*?\*\*Target\*\*\s*\|\s*`([^`]+)`/i,
    /"target"\s*:\s*"([^"]+)"/i,
  ]);

  const id = pick(markdown, [
    /\|\s*\*\*Finding ID\*\*\s*\|\s*`([^`]+)`/i,
    /"id"\s*:\s*"([^"]+)"/i,
  ]);

  const title = pick(markdown, [
    /\|\s*\*\*Title\*\*\s*\|\s*(.+?)\s*\|/i,
    /### 🌐 Target Information[\s\S]*?\*\*Title\*\*\s*\|\s*(.+?)\s*\|/i,
    /## 🛡️[^\n]*\n[\s\S]*?\*\*Title\*\*\s*\|\s*(.+?)\s*\|/i,
  ]);

  const endpoint = pick(markdown, [
    /\*\*Affected Endpoint:\*\*\s*`([^`]+)`/i,
    /"endpoint"\s*:\s*"([^"]+)"/i,
  ]);

  const observation = pick(markdown, [
    /\*\*Observation:\*\*\s*(.+?)(?=\n\*|\n---|\n###|$)/is,
    /"observation"\s*:\s*"([^"]+)"/i,
  ]);

  const evidence = pick(markdown, [
    /\*\*Evidence of Exploitation:\*\*\s*(.+?)(?=\n\*|\n---|\n###|$)/is,
    /"evidence"\s*:\s*"([^"]+)"/i,
  ]);

  const notes = pick(markdown, [
    /\*\*Analysis & Notes:\*\*\s*(.+?)(?=\n---|\n###|$)/is,
    /"notes"\s*:\s*"([^"]+)"/i,
  ]);

  const owasp = pick(markdown, [
    /\*\*OWASP Category\*\*\s*\|\s*(.+?)\s*\|/i,
    /"owasp"\s*:\s*"([^"]+)"/i,
  ]);

  const wstg = pick(markdown, [
    /\*\*WSTG Reference\*\*\s*\|\s*(.+?)\s*\|/i,
    /"wstg"\s*:\s*"([^"]+)"/i,
  ]);

  const steps = pickList(markdown, /### 🪜 Steps to Reproduce\s*\n([\s\S]*?)(?=\n---|\n###|$)/i);
  const remediation = pickList(
    markdown,
    /### 🔧 Remediation Recommendations\s*\n([\s\S]*?)(?=\n---|\n###|$)/i,
  );

  const request_evidence =
    pickCodeBlock(markdown) ||
    pick(markdown, [/\"request_evidence\"\s*:\s*\"([^\"]+)\"/i]);

  return {
    target: target || "unknown-target",
    finding: {
      id: id || undefined,
      title: title || "Transferred Finding",
      severity: pickSeverity(markdown),
      owasp,
      wstg,
      endpoint: endpoint || "/",
      observation: observation || "See transferred report for details.",
      evidence: evidence || notes || observation || "Transferred from chat report.",
      steps_to_reproduce: steps,
      notes: notes || "",
      remediation: remediation.some(Boolean) ? remediation : [""],
      request_evidence: request_evidence || "",
    },
  };
}

export function getMessageText(message: {
  parts?: Array<{ type: string; text?: string }>;
}): string {
  return (
    message.parts
      ?.filter((p) => p.type === "text" && p.text)
      .map((p) => p.text)
      .join("\n") ?? ""
  );
}
