import { Copy, Download, FileText } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  downloadReportFile,
  reportToMarkdownText,
  type GenerateReportResponse,
} from "@/services/reportApi";

function severityVariant(severity: string): "destructive" | "default" | "secondary" | "outline" {
  const s = severity.toUpperCase();
  if (s.includes("CRITICAL") || s.includes("HIGH")) return "destructive";
  if (s.includes("MEDIUM")) return "default";
  return "secondary";
}

interface ReportViewerProps {
  report: GenerateReportResponse;
}

export function ReportViewer({ report }: ReportViewerProps) {
  const handleCopy = async () => {
    const text = report.markdown || reportToMarkdownText(report);
    await navigator.clipboard.writeText(text);
    toast.success("Report copied to clipboard");
  };

  const handleDownloadMarkdown = () => {
    const content = report.markdown || reportToMarkdownText(report);
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = report.markdown_filename ?? `${report.title.slice(0, 40)}.md`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    toast.success("Markdown downloaded");
  };

  const handleDownloadDocx = async () => {
    if (!report.docx_filename) {
      toast.error("DOCX file not available");
      return;
    }
    try {
      await downloadReportFile(report.docx_filename, report.docx_filename);
      toast.success("Word report downloaded");
    } catch {
      toast.error("Failed to download DOCX");
    }
  };

  return (
    <Card className="border-border/60">
      <CardHeader className="pb-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-2">
            <CardTitle className="text-base font-semibold leading-snug">
              {report.section_number ? `${report.section_number} ` : ""}
              {report.title}
            </CardTitle>
            <div className="flex flex-wrap gap-2">
              <Badge variant={severityVariant(report.severity)}>{report.severity}</Badge>
              {report.finding_id && (
                <Badge variant="outline" className="font-mono">
                  {report.finding_id}
                </Badge>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={handleCopy}>
              <Copy className="mr-1.5 h-3.5 w-3.5" />
              Copy
            </Button>
            <Button variant="outline" size="sm" onClick={handleDownloadMarkdown}>
              <FileText className="mr-1.5 h-3.5 w-3.5" />
              Markdown
            </Button>
            <Button variant="outline" size="sm" onClick={handleDownloadDocx}>
              <Download className="mr-1.5 h-3.5 w-3.5" />
              DOCX
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6 text-sm">
        <div className="grid gap-3 sm:grid-cols-2">
          <MetaField label="OWASP" value={report.owasp} />
          <MetaField label="CWE" value={report.cwe} />
          {report.wstg && <MetaField label="WSTG" value={report.wstg} />}
          {report.cvss_score != null && (
            <MetaField label="CVSS v3.1" value={String(report.cvss_score)} />
          )}
        </div>

        <Separator />

        <Section title="Description" body={report.description} />
        <Section title="Technical Impact" body={report.technical_impact} />
        <Section title="Business Impact" body={report.business_impact} />

        {report.affected_endpoints && report.affected_endpoints.length > 0 && (
          <div>
            <h3 className="mb-2 font-semibold">Affected Endpoints</h3>
            <div className="overflow-x-auto rounded-md border">
              <table className="w-full text-xs">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium">Endpoint</th>
                    <th className="px-3 py-2 text-left font-medium">Roles</th>
                    <th className="px-3 py-2 text-left font-medium">Impact</th>
                    <th className="px-3 py-2 text-left font-medium">Severity</th>
                  </tr>
                </thead>
                <tbody>
                  {report.affected_endpoints.map((row, i) => (
                    <tr key={i} className="border-t">
                      <td className="px-3 py-2 font-mono">{row.endpoint}</td>
                      <td className="px-3 py-2">{row.affected_roles}</td>
                      <td className="px-3 py-2">{row.impact}</td>
                      <td className="px-3 py-2">{row.severity}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div>
          <h3 className="mb-2 font-semibold">Steps to Reproduce</h3>
          <ol className="list-decimal space-y-1.5 pl-5 text-muted-foreground">
            {report.steps_to_reproduce.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </div>

        {report.proof_of_concept && (
          <div>
            <h3 className="mb-2 font-semibold">Proof of Concept</h3>
            <pre className="overflow-x-auto rounded-md border bg-muted/30 p-3 font-mono text-xs leading-relaxed">
              {report.proof_of_concept}
            </pre>
          </div>
        )}

        <div>
          <h3 className="mb-2 font-semibold">Remediation</h3>
          <ul className="list-disc space-y-1.5 pl-5 text-muted-foreground">
            {report.remediation.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>

        {report.references.length > 0 && (
          <div>
            <h3 className="mb-2 font-semibold">References</h3>
            <ul className="list-disc space-y-1 pl-5 text-muted-foreground">
              {report.references.map((ref, i) => (
                <li key={i}>{ref}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function MetaField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-muted/20 px-3 py-2">
      <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="mt-0.5 text-sm">{value || "N/A"}</p>
    </div>
  );
}

function Section({ title, body }: { title: string; body: string }) {
  if (!body) return null;
  return (
    <div>
      <h3 className="mb-2 font-semibold">{title}</h3>
      <p className="leading-relaxed text-muted-foreground whitespace-pre-wrap">{body}</p>
    </div>
  );
}
