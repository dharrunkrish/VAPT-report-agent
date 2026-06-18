"use client";

import { Copy, Download, Eye, FileText, Pencil } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Streamdown } from "streamdown";
import { cjk } from "@streamdown/cjk";
import { code } from "@streamdown/code";
import { math } from "@streamdown/math";
import { mermaid } from "@streamdown/mermaid";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
  downloadReportFile,
  type GenerateReportResponse,
} from "@/services/reportApi";

const streamdownPlugins = { cjk, code, math, mermaid };

interface EditableReportViewerProps {
  report: GenerateReportResponse;
  markdown: string;
  onMarkdownChange: (value: string) => void;
}

export function EditableReportViewer({
  report,
  markdown,
  onMarkdownChange,
}: EditableReportViewerProps) {
  const [panel, setPanel] = useState<"split" | "edit" | "preview">("split");

  const handleCopy = async () => {
    await navigator.clipboard.writeText(markdown);
    toast.success("Markdown copied to clipboard");
  };

  const handleDownloadMd = () => {
    const blob = new Blob([markdown], { type: "text/markdown" });
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
      toast.error("DOCX file not available from backend");
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
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle className="text-base">{report.title}</CardTitle>
          <div className="flex flex-wrap gap-2">
            <Button
              variant={panel === "edit" ? "secondary" : "outline"}
              size="sm"
              onClick={() => setPanel(panel === "edit" ? "split" : "edit")}
              className="lg:hidden"
            >
              <Pencil className="mr-1.5 h-3.5 w-3.5" />
              Edit
            </Button>
            <Button
              variant={panel === "preview" ? "secondary" : "outline"}
              size="sm"
              onClick={() => setPanel(panel === "preview" ? "split" : "preview")}
              className="lg:hidden"
            >
              <Eye className="mr-1.5 h-3.5 w-3.5" />
              Preview
            </Button>
            <Button variant="outline" size="sm" onClick={handleCopy}>
              <Copy className="mr-1.5 h-3.5 w-3.5" />
              Copy Markdown
            </Button>
            <Button variant="outline" size="sm" onClick={handleDownloadMd}>
              <FileText className="mr-1.5 h-3.5 w-3.5" />
              Download .md
            </Button>
            <Button variant="outline" size="sm" onClick={handleDownloadDocx}>
              <Download className="mr-1.5 h-3.5 w-3.5" />
              Export DOCX
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div
          className={cn(
            "grid gap-4",
            panel === "split" && "lg:grid-cols-2",
            panel === "edit" && "grid-cols-1",
            panel === "preview" && "grid-cols-1",
          )}
        >
          {(panel === "split" || panel === "edit") && (
            <Textarea
              value={markdown}
              onChange={(e) => onMarkdownChange(e.target.value)}
              className="min-h-[520px] font-mono text-xs leading-relaxed"
              spellCheck={false}
            />
          )}
          {(panel === "split" || panel === "preview") && (
            <div className="min-h-[520px] overflow-auto rounded-md border bg-background p-4 text-sm">
              <Streamdown plugins={streamdownPlugins}>{markdown}</Streamdown>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
