export interface ParsedFindingForm {
  target: string;
  finding: {
    endpoint: string;
    observation: string;
    evidence: string;
    notes: string;
    request_evidence: string;
  };
}

function pick(markdown: string, patterns: RegExp[]): string {
  for (const pattern of patterns) {
    const match = markdown.match(pattern);
    if (match?.[1]?.trim()) return match[1].trim();
  }
  return "";
}

function pickCodeBlock(markdown: string): string {
  const httpBlock = markdown.match(
    /### 💻 Technical Proof of Concept[\s\S]*?```(?:http)?\n([\s\S]*?)```/i,
  );
  if (httpBlock?.[1]) return httpBlock[1].trim();

  const anyBlock = markdown.match(/```(?:http)?\n([\s\S]*?)```/);
  return anyBlock?.[1]?.trim() ?? "";
}

export function parseReportMarkdown(markdown: string): ParsedFindingForm {
  const target = pick(markdown, [
    /\|\s*\*\*Target\*\*\s*\|\s*`([^`]+)`/i,
    /Target Information[\s\S]*?\*\*Target\*\*\s*\|\s*`([^`]+)`/i,
    /"target"\s*:\s*"([^"]+)"/i,
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

  const request_evidence = pickCodeBlock(markdown) || pick(markdown, [
    /"request_evidence"\s*:\s*"([^"]+)"/i,
  ]);

  return {
    target: target || "unknown-target",
    finding: {
      endpoint: endpoint || "/",
      observation: observation || "See transferred report for details.",
      evidence: evidence || notes || observation || "Transferred from chat report.",
      notes: notes || "",
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
