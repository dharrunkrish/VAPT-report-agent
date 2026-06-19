import {
  Download,
  Eye,
  FileText,
  GripVertical,
  Plus,
  Trash2,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Streamdown } from "streamdown";
import { cjk } from "@streamdown/cjk";
import { code } from "@streamdown/code";
import { math } from "@streamdown/math";
import { mermaid } from "@streamdown/mermaid";

import { FindingFormFields } from "@/components/findings/FindingFormFields";
import { JsonUploadZone } from "@/components/findings/JsonUploadZone";
import { SeverityBadge } from "@/components/findings/SeverityBadge";
import { SeveritySummaryBar } from "@/components/findings/SeveritySummaryBar";
import { AppHeader } from "@/components/layout/AppHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { useGenerateReport } from "@/hooks/useGenerateReport";
import { findingToApiPayload } from "@/lib/findingsJson";
import { parseReportMarkdown } from "@/lib/parseReportMarkdown";
import {
  downloadReportFile,
  findingsToPreviewMarkdown,
} from "@/services/reportApi";
import {
  emptyFinding,
  useFindingsStore,
  type Finding,
} from "@/store/findingsStore";
import { cn } from "@/lib/utils";

const streamdownPlugins = { cjk, code, math, mermaid };

export function FindingsManager() {
  const {
    target,
    findings,
    setTarget,
    addFinding,
    updateFinding,
    removeFinding,
    reorderFindings,
    importFindings,
    clearAll,
  } = useFindingsStore();

  const { isLoading, generateFromFindings } = useGenerateReport();
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [editor, setEditor] = useState<Finding>(emptyFinding());
  const [previewOpen, setPreviewOpen] = useState(false);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const transferApplied = useRef(false);

  useEffect(() => {
    if (transferApplied.current) return;
    const raw = sessionStorage.getItem("vapt-chat-transfer-v1");
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as ReturnType<typeof parseReportMarkdown>;
        importFindings(parsed.target, [parsed.finding]);
        setSelectedIndex(0);
        setEditor(parsed.finding);
        sessionStorage.removeItem("vapt-chat-transfer-v1");
        transferApplied.current = true;
      } catch {
        /* ignore */
      }
    }
  }, [importFindings]);

  useEffect(() => {
    if (selectedIndex !== null && findings[selectedIndex]) {
      setEditor(findings[selectedIndex]);
    }
  }, [selectedIndex, findings]);

  const saveEditor = () => {
    if (selectedIndex === null) {
      if (!editor.title.trim()) {
        toast.error("Title is required");
        return;
      }
      addFinding({ ...editor });
      setSelectedIndex(findings.length);
      toast.success("Finding added");
      return;
    }
    updateFinding(selectedIndex, { ...editor });
    toast.success("Finding saved");
  };

  const handleNewFinding = () => {
    setSelectedIndex(null);
    setEditor(emptyFinding());
  };

  const handleImport = (importTarget: string, imported: Finding[]) => {
    importFindings(importTarget || target, imported);
    if (importTarget) setTarget(importTarget);
    if (imported.length > 0) {
      setSelectedIndex(0);
      setEditor(imported[0]);
    }
  };

  const exportJson = () => {
    const payload = {
      target,
      findings: findings.map(findingToApiPayload),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${target || "findings"}_export.json`;
    anchor.click();
    URL.revokeObjectURL(url);
    toast.success("Findings JSON exported");
  };

  const handleGenerateDocx = async () => {
    if (!target.trim() || findings.length === 0) {
      toast.error("Target and at least one finding required");
      return;
    }
    try {
      const result = await generateFromFindings(target, findings);
      if (result.docx_filename) {
        await downloadReportFile(result.docx_filename, result.docx_filename);
      }
    } catch {
      /* toast handled in hook */
    }
  };

  const previewMarkdown = findingsToPreviewMarkdown(
    target,
    findings.map(findingToApiPayload),
  );

  return (
    <div className="flex min-h-screen flex-col">
      <AppHeader
        title="Findings Manager"
        subtitle="edit · reorder · preview · export"
        actions={
          findings.length > 0 ? (
            <Button variant="ghost" size="sm" onClick={clearAll} className="text-muted-foreground">
              <Trash2 className="mr-1.5 h-3.5 w-3.5" />
              Clear All
            </Button>
          ) : null
        }
      />

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-4 px-4 py-6 pb-28">
        <JsonUploadZone onImport={handleImport} />

        <div className="grid flex-1 gap-4 lg:grid-cols-[320px_1fr]">
          <Card className="border-border/60">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Findings List</CardTitle>
                <Button variant="outline" size="sm" onClick={handleNewFinding}>
                  <Plus className="mr-1 h-3.5 w-3.5" />
                  Add New
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {findings.length === 0 ? (
                <p className="text-sm text-muted-foreground">No findings yet. Import JSON or add one.</p>
              ) : (
                findings.map((finding, index) => (
                  <div
                    key={`${finding.id ?? finding.title}-${index}`}
                    draggable
                    onDragStart={() => setDragIndex(index)}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={() => {
                      if (dragIndex !== null && dragIndex !== index) {
                        reorderFindings(dragIndex, index);
                      }
                      setDragIndex(null);
                    }}
                    className={cn(
                      "flex cursor-pointer items-start gap-2 rounded-md border p-2 transition-colors",
                      selectedIndex === index ? "border-primary bg-primary/5" : "hover:bg-muted/40",
                    )}
                    onClick={() => setSelectedIndex(index)}
                  >
                    <GripVertical className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[10px] text-muted-foreground">{index + 1}.</span>
                        <SeverityBadge severity={finding.severity} />
                      </div>
                      <p className="truncate text-sm font-medium">{finding.title}</p>
                      <p className="truncate font-mono text-[10px] text-muted-foreground">
                        {finding.endpoint || "No endpoint"}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="shrink-0 text-muted-foreground hover:text-destructive"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeFinding(index);
                        if (selectedIndex === index) {
                          setSelectedIndex(null);
                          setEditor(emptyFinding());
                        }
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card className="border-border/60">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">
                {selectedIndex === null ? "New Finding" : `Edit Finding ${selectedIndex + 1}`}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="fm-target">Target</Label>
                <Input
                  id="fm-target"
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  placeholder="example.com"
                />
              </div>
              <FindingFormFields
                finding={editor}
                onChange={setEditor}
                showAiAssist
              />
              <Button onClick={saveEditor}>
                {selectedIndex === null ? "Add Finding" : "Save Changes"}
              </Button>
            </CardContent>
          </Card>
        </div>

        {previewOpen && (
          <Card className="border-border/60">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle className="text-base">Report Preview</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setPreviewOpen(false)}>
                Close
              </Button>
            </CardHeader>
            <CardContent className="max-h-[480px] overflow-auto rounded-md border p-4 text-sm">
              <Streamdown plugins={streamdownPlugins}>{previewMarkdown}</Streamdown>
            </CardContent>
          </Card>
        )}
      </main>

      <div className="fixed bottom-0 left-0 right-0 border-t bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <SeveritySummaryBar findings={findings} />
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={() => setPreviewOpen((v) => !v)} disabled={findings.length === 0}>
              <Eye className="mr-1.5 h-3.5 w-3.5" />
              Preview Report
            </Button>
            <Button variant="outline" size="sm" onClick={exportJson} disabled={findings.length === 0}>
              <Download className="mr-1.5 h-3.5 w-3.5" />
              Export Findings JSON
            </Button>
            <Button size="sm" onClick={handleGenerateDocx} disabled={isLoading || findings.length === 0}>
              {isLoading ? (
                <>
                  <Spinner className="mr-2" />
                  Generating…
                </>
              ) : (
                <>
                  <FileText className="mr-1.5 h-3.5 w-3.5" />
                  Generate Full DOCX Report
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
