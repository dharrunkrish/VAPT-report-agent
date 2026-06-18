import { Link } from "@tanstack/react-router";
import { ShieldCheck, Sparkles, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import logo from "@/assets/vapt-logo.png";
import { EditableReportViewer } from "@/components/EditableReportViewer";
import { ThinkingIndicator } from "@/components/ThinkingIndicator";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { useGenerateReport } from "@/hooks/useGenerateReport";
import type { GenerateReportRequest } from "@/services/reportApi";
import { consumeTransferPayload } from "@/stores/reportTransferStore";

const EMPTY_FORM: GenerateReportRequest = {
  target: "",
  finding: {
    endpoint: "",
    observation: "",
    evidence: "",
    notes: "",
    request_evidence: "",
  },
};

const SAMPLE_FORM: GenerateReportRequest = {
  target: "example.com",
  finding: {
    endpoint: "/api/user/123",
    observation:
      "The application does not enforce strong password requirements at the backend for forgot password and reset password functionalities.",
    evidence:
      "It was observed that by directly interacting with the API endpoint, users can bypass UI restrictions and set weak and easily guessable passwords.",
    notes: "This indicates that password policy enforcement is not implemented on the server side.",
    request_evidence:
      "POST /auth/accounts/dbcddca3-c040-41a0-95fa-83149935d065/set-password-by-token",
  },
};

export function ReportGenerator() {
  const {
    report,
    markdown,
    isLoading,
    error,
    generate,
    updateMarkdown,
    clearReport,
  } = useGenerateReport();
  const [form, setForm] = useState<GenerateReportRequest>(EMPTY_FORM);

  useEffect(() => {
    const transferred = consumeTransferPayload();
    if (transferred) {
      setForm(transferred);
    }
  }, []);

  const updateFinding = (field: keyof NonNullable<GenerateReportRequest["finding"]>, value: string) => {
    setForm((prev) => ({
      ...prev,
      finding: { ...(prev.finding ?? EMPTY_FORM.finding!), [field]: value },
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.target.trim() || !form.finding?.observation.trim()) return;
    await generate(form);
  };

  const loadSample = () => setForm(SAMPLE_FORM);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-border/60 bg-background/70 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <img src={logo} alt="VAPT shield logo" width={36} height={36} className="h-9 w-9" />
            <div className="flex flex-col leading-tight">
              <h1 className="text-sm font-semibold tracking-tight text-foreground">
                VAPT Report Generator
              </h1>
              <p className="text-xs text-muted-foreground font-mono">
                structured_input → crewai_pipeline → docx
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild>
              <Link to="/">Chat</Link>
            </Button>
            {report && (
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
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="border-border/60 h-fit">
            <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle className="text-base">Submit Finding</CardTitle>
                <CardDescription>
                  Sends structured input to the Python CrewAI backend for enterprise-grade
                  report generation.
                </CardDescription>
              </div>
              <Button variant="outline" size="sm" type="button" onClick={loadSample}>
                <Sparkles className="mr-1.5 h-3.5 w-3.5" />
                Load sample
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="target">Target</Label>
                <Input
                  id="target"
                  placeholder="example.com"
                  value={form.target}
                  onChange={(e) => setForm((p) => ({ ...p, target: e.target.value }))}
                  required
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="endpoint">Endpoint</Label>
                <Input
                  id="endpoint"
                  placeholder="/api/user/123"
                  value={form.finding?.endpoint ?? ""}
                  onChange={(e) => updateFinding("endpoint", e.target.value)}
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="observation">Observation</Label>
                <Textarea
                  id="observation"
                  placeholder="Describe the vulnerability..."
                  value={form.finding?.observation ?? ""}
                  onChange={(e) => updateFinding("observation", e.target.value)}
                  className="min-h-[80px]"
                  required
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="evidence">Evidence</Label>
                <Textarea
                  id="evidence"
                  placeholder="Evidence of exploitation..."
                  value={form.finding?.evidence ?? ""}
                  onChange={(e) => updateFinding("evidence", e.target.value)}
                  className="min-h-[80px]"
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  placeholder="Additional analysis notes..."
                  value={form.finding?.notes ?? ""}
                  onChange={(e) => updateFinding("notes", e.target.value)}
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="request_evidence">Request Evidence</Label>
                <Textarea
                  id="request_evidence"
                  placeholder="POST /auth/..."
                  value={form.finding?.request_evidence ?? ""}
                  onChange={(e) => updateFinding("request_evidence", e.target.value)}
                  className="font-mono text-xs min-h-[80px]"
                  disabled={isLoading}
                />
              </div>

              {error && (
                <div className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {error}
                </div>
              )}

              <Button type="submit" disabled={isLoading} className="w-full sm:w-auto">
                {isLoading ? (
                  <>
                    <Spinner className="mr-2" />
                    Generating…
                  </>
                ) : (
                  <>
                    <ShieldCheck className="mr-2 h-4 w-4" />
                    Generate VAPT Finding
                  </>
                )}
              </Button>
            </form>
          </CardContent>
          </Card>

          {isLoading && <ThinkingIndicator isActive className="lg:col-span-2" />}
        </div>

        {report && !isLoading && (
          <div className="mt-6">
            <EditableReportViewer
              report={report}
              markdown={markdown}
              onMarkdownChange={updateMarkdown}
            />
          </div>
        )}
      </main>
    </div>
  );
}
