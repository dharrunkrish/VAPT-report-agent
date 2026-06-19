import { Sparkles, Wand2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { DynamicStringList } from "@/components/findings/DynamicStringList";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { requestChatCompletion } from "@/lib/chatAssist";
import { SEVERITY_OPTIONS, severityBadgeClass } from "@/lib/severity";
import type { Finding, Severity } from "@/store/findingsStore";
import { cn } from "@/lib/utils";

interface FindingFormFieldsProps {
  finding: Finding;
  onChange: (finding: Finding) => void;
  disabled?: boolean;
  showAiAssist?: boolean;
}

type FieldKey = keyof Finding;

const FIELD_LABELS: Record<string, string> = {
  id: "Finding ID",
  title: "Title",
  severity: "Severity",
  owasp: "OWASP",
  wstg: "WSTG",
  endpoint: "Endpoint",
  observation: "Observation",
  evidence: "Evidence",
  notes: "Notes / Analysis",
  request_evidence: "Request Evidence",
};

export function FindingFormFields({
  finding,
  onChange,
  disabled,
  showAiAssist = false,
}: FindingFormFieldsProps) {
  const [aiLoading, setAiLoading] = useState<string | null>(null);

  const patch = (partial: Partial<Finding>) => onChange({ ...finding, ...partial });

  const runAiAssist = async (field: FieldKey) => {
    const label = FIELD_LABELS[field] ?? field;
    const current =
      field === "steps_to_reproduce"
        ? (finding.steps_to_reproduce ?? []).join("\n")
        : field === "remediation"
          ? (finding.remediation ?? []).join("\n")
          : String(finding[field] ?? "");

    if (!current.trim()) {
      toast.error(`Enter a value for ${label} first`);
      return;
    }

    setAiLoading(field);
    try {
      const result = await requestChatCompletion(
        `Improve this ${label} for a VAPT report. Return ONLY the improved text, no preamble:\n\n${current}`,
      );
      if (field === "steps_to_reproduce") {
        patch({ steps_to_reproduce: result.split("\n").filter(Boolean) });
      } else if (field === "remediation") {
        patch({ remediation: result.split("\n").filter(Boolean) });
      } else {
        patch({ [field]: result } as Partial<Finding>);
      }
      toast.success(`${label} updated`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "AI assist failed");
    } finally {
      setAiLoading(null);
    }
  };

  const runAutoFill = async () => {
    setAiLoading("autofill");
    try {
      const prompt = `Given this partial VAPT finding data, infer and fill ALL missing fields. Return ONLY valid JSON with keys: id, title, severity, owasp, wstg, endpoint, observation, evidence, steps_to_reproduce (array), notes, remediation (array), request_evidence.

Current data:
${JSON.stringify(finding, null, 2)}`;
      const result = await requestChatCompletion(prompt);
      const jsonMatch = result.match(/\{[\s\S]*\}/);
      if (!jsonMatch) throw new Error("AI did not return JSON");
      const parsed = JSON.parse(jsonMatch[0]) as Partial<Finding>;
      patch({
        id: finding.id || parsed.id,
        title: finding.title || parsed.title || finding.title,
        severity: finding.severity || (parsed.severity as Severity) || "MEDIUM",
        owasp: finding.owasp || parsed.owasp || "",
        wstg: finding.wstg || parsed.wstg || "",
        endpoint: finding.endpoint || parsed.endpoint || "",
        observation: finding.observation || parsed.observation || "",
        evidence: finding.evidence || parsed.evidence || "",
        steps_to_reproduce:
          finding.steps_to_reproduce?.some(Boolean)
            ? finding.steps_to_reproduce
            : parsed.steps_to_reproduce ?? [""],
        notes: finding.notes || parsed.notes || "",
        remediation:
          finding.remediation?.some(Boolean) ? finding.remediation : parsed.remediation ?? [""],
        request_evidence: finding.request_evidence || parsed.request_evidence || "",
      });
      toast.success("Empty fields auto-filled");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Auto-fill failed");
    } finally {
      setAiLoading(null);
    }
  };

  const AiBtn = ({ field }: { field: FieldKey }) =>
    showAiAssist ? (
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="h-7 px-2 text-xs"
        disabled={disabled || aiLoading !== null}
        onClick={() => runAiAssist(field)}
      >
        <Sparkles className="mr-1 h-3 w-3" />
        {aiLoading === field ? "…" : "AI Assist"}
      </Button>
    ) : null;

  return (
    <div className="space-y-4">
      {showAiAssist && (
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={disabled || aiLoading !== null}
          onClick={runAutoFill}
        >
          <Wand2 className="mr-1.5 h-3.5 w-3.5" />
          {aiLoading === "autofill" ? "Auto-filling…" : "Auto-fill with AI"}
        </Button>
      )}

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="finding-id">Finding ID</Label>
          <AiBtn field="id" />
        </div>
        <Input
          id="finding-id"
          placeholder="e.g. XPCON-2026-001 (optional)"
          value={finding.id ?? ""}
          onChange={(e) => patch({ id: e.target.value })}
          disabled={disabled}
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="finding-title">Title</Label>
          <AiBtn field="title" />
        </div>
        <Input
          id="finding-title"
          placeholder="e.g. IDOR on User Profile Endpoint"
          value={finding.title}
          onChange={(e) => patch({ title: e.target.value })}
          required
          disabled={disabled}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="finding-severity">Severity</Label>
        <Select
          value={finding.severity}
          onValueChange={(v) => patch({ severity: v as Severity })}
          disabled={disabled}
        >
          <SelectTrigger
            id="finding-severity"
            className={cn(severityBadgeClass(finding.severity), "font-semibold")}
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SEVERITY_OPTIONS.map((sev) => (
              <SelectItem key={sev} value={sev}>
                <span className={cn("rounded px-1.5 py-0.5 text-xs", severityBadgeClass(sev))}>
                  {sev}
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="finding-owasp">OWASP</Label>
          <AiBtn field="owasp" />
        </div>
        <Input
          id="finding-owasp"
          placeholder="e.g. Broken Access Control (OWASP A01:2025)"
          value={finding.owasp ?? ""}
          onChange={(e) => patch({ owasp: e.target.value })}
          disabled={disabled}
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="finding-wstg">WSTG</Label>
          <AiBtn field="wstg" />
        </div>
        <Input
          id="finding-wstg"
          placeholder="e.g. WSTG-ATHZ-03"
          value={finding.wstg ?? ""}
          onChange={(e) => patch({ wstg: e.target.value })}
          disabled={disabled}
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="finding-endpoint">Endpoint</Label>
          <AiBtn field="endpoint" />
        </div>
        <Input
          id="finding-endpoint"
          placeholder="/api/user/123"
          value={finding.endpoint ?? ""}
          onChange={(e) => patch({ endpoint: e.target.value })}
          disabled={disabled}
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="finding-observation">Observation</Label>
          <AiBtn field="observation" />
        </div>
        <Textarea
          id="finding-observation"
          placeholder="Describe the vulnerability..."
          value={finding.observation ?? ""}
          onChange={(e) => patch({ observation: e.target.value })}
          className="min-h-[80px]"
          required
          disabled={disabled}
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="finding-evidence">Evidence</Label>
          <AiBtn field="evidence" />
        </div>
        <Textarea
          id="finding-evidence"
          placeholder="Evidence of exploitation..."
          value={finding.evidence ?? ""}
          onChange={(e) => patch({ evidence: e.target.value })}
          className="min-h-[80px]"
          disabled={disabled}
        />
      </div>

      <DynamicStringList
        label="Steps to Reproduce"
        values={finding.steps_to_reproduce ?? [""]}
        onChange={(steps_to_reproduce) => patch({ steps_to_reproduce })}
        addLabel="Add Step"
        placeholder="Describe step..."
        disabled={disabled}
      />

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="finding-notes">Notes / Analysis</Label>
          <AiBtn field="notes" />
        </div>
        <Textarea
          id="finding-notes"
          placeholder="Technical analysis, root cause notes..."
          value={finding.notes ?? ""}
          onChange={(e) => patch({ notes: e.target.value })}
          disabled={disabled}
        />
      </div>

      <DynamicStringList
        label="Remediation"
        values={finding.remediation ?? [""]}
        onChange={(remediation) => patch({ remediation })}
        addLabel="Add Recommendation"
        placeholder="Remediation action..."
        disabled={disabled}
      />

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="finding-request">Request Evidence</Label>
          <AiBtn field="request_evidence" />
        </div>
        <Textarea
          id="finding-request"
          placeholder="POST /auth/..."
          value={finding.request_evidence ?? ""}
          onChange={(e) => patch({ request_evidence: e.target.value })}
          className="min-h-[80px] font-mono text-xs"
          disabled={disabled}
        />
      </div>
    </div>
  );
}
