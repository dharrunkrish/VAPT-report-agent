import { Plus, ShieldCheck, Sparkles, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { FindingFormFields } from "@/components/findings/FindingFormFields";
import { FindingsQueuePanel } from "@/components/findings/FindingsQueuePanel";
import { JsonUploadZone } from "@/components/findings/JsonUploadZone";
import { EditableReportViewer } from "@/components/EditableReportViewer";
import { ThinkingIndicator } from "@/components/ThinkingIndicator";
import { AppHeader } from "@/components/layout/AppHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { useGenerateReport } from "@/hooks/useGenerateReport";
import { parseReportMarkdown } from "@/lib/parseReportMarkdown";
import { consumeTransferPayload } from "@/stores/reportTransferStore";
import {
  emptyFinding,
  SAMPLE_FINDING,
  SAMPLE_TARGET,
  useFindingsStore,
  type Finding,
} from "@/store/findingsStore";

export function ReportGenerator() {
  const {
    target,
    findings,
    setTarget,
    addFinding,
    removeFinding,
    importFindings,
  } = useFindingsStore();

  const {
    report,
    markdown,
    isLoading,
    error,
    generateFromFindings,
    updateMarkdown,
    clearReport,
  } = useGenerateReport();

  const [draft, setDraft] = useState<Finding>(emptyFinding());

  useEffect(() => {
    const transferred = consumeTransferPayload();
      if (transferred) {
        setTarget(transferred.target);
        setDraft(transferred.finding);
        importFindings(transferred.target, [transferred.finding]);
      }
  }, [importFindings, setTarget]);

  const loadSample = () => {
    setTarget(SAMPLE_TARGET);
    setDraft({ ...SAMPLE_FINDING });
  };

  const addDraftToQueue = () => {
    if (!draft.title.trim() || !draft.observation?.trim()) {
      toast.error("Title and Observation are required");
      return;
    }
    addFinding({ ...draft });
    setDraft(emptyFinding());
    toast.success("Finding added to queue");
  };

  const handleGenerateAll = async () => {
    if (!target.trim()) {
      toast.error("Target is required");
      return;
    }
    if (findings.length === 0) {
      toast.error("Add at least one finding to the queue");
      return;
    }
    await generateFromFindings(target, findings);
  };

  const handleImport = (importTarget: string, imported: Finding[]) => {
    importFindings(importTarget || target, imported);
    if (importTarget) setTarget(importTarget);
  };

  return (
    <div className="flex min-h-screen flex-col">
      <AppHeader
        title="VAPT Report Generator"
        subtitle="structured_input → crewai_pipeline → docx"
        actions={
          report ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearReport}
              disabled={isLoading}
              className="text-muted-foreground hover:text-foreground"
            >
              <Trash2 className="mr-1.5 h-3.5 w-3.5" />
              Clear
            </Button>
          ) : null
        }
      />

      <main className="mx-auto w-full max-w-6xl flex-1 space-y-6 px-4 py-6">
        <JsonUploadZone onImport={handleImport} />

        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="border-border/60 h-fit">
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-base">Submit Finding</CardTitle>
                  <CardDescription>
                    Add findings to the queue, then generate a full CrewAI report.
                  </CardDescription>
                </div>
                <Button variant="outline" size="sm" type="button" onClick={loadSample}>
                  <Sparkles className="mr-1.5 h-3.5 w-3.5" />
                  Load sample
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="target">Target</Label>
                <Input
                  id="target"
                  placeholder="example.com"
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>

              <FindingFormFields
                finding={draft}
                onChange={setDraft}
                disabled={isLoading}
              />

              {error && (
                <div className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {error}
                </div>
              )}

              <div className="flex flex-wrap gap-2">
                <Button type="button" variant="outline" onClick={addDraftToQueue} disabled={isLoading}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" />
                  Add to Queue
                </Button>
                <Button type="button" onClick={handleGenerateAll} disabled={isLoading || findings.length === 0}>
                  {isLoading ? (
                    <>
                      <Spinner className="mr-2" />
                      Generating…
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="mr-2 h-4 w-4" />
                      Generate Full Report
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          <FindingsQueuePanel
            findings={findings}
            onRemove={removeFinding}
            onAddAnother={() => setDraft(emptyFinding())}
          />

          {isLoading && <ThinkingIndicator isActive className="lg:col-span-2" />}
        </div>

        {report && !isLoading && (
          <EditableReportViewer
            report={report}
            markdown={markdown}
            onMarkdownChange={updateMarkdown}
          />
        )}
      </main>
    </div>
  );
}
