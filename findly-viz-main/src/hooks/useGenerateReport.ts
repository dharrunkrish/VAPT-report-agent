import { useCallback, useState } from "react";
import { toast } from "sonner";

import {
  generateReport,
  reportToMarkdownText,
  type GenerateReportRequest,
  type GenerateReportResponse,
  ReportApiError,
} from "@/services/reportApi";
import { findingToApiPayload } from "@/lib/findingsJson";
import type { Finding } from "@/store/findingsStore";

const STORAGE_KEY = "vapt-generated-report-v1";
const MARKDOWN_KEY = "vapt-generated-markdown-v1";

export function useGenerateReport() {
  const [report, setReport] = useState<GenerateReportResponse | null>(() => {
    if (typeof window === "undefined") return null;
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as GenerateReportResponse) : null;
    } catch {
      return null;
    }
  });
  const [markdown, setMarkdown] = useState<string>(() => {
    if (typeof window === "undefined") return "";
    return localStorage.getItem(MARKDOWN_KEY) ?? "";
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateFromFindings = useCallback(
    async (target: string, findings: Finding[]) => {
      if (!target.trim()) throw new Error("Target is required");
      if (findings.length === 0) throw new Error("Add at least one finding");

      setIsLoading(true);
      setError(null);

      try {
        const result = await generateReport({
          target,
          findings: findings.map(findingToApiPayload),
        });

        const md = result.markdown || reportToMarkdownText(result);
        setReport(result);
        setMarkdown(md);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(result));
        localStorage.setItem(MARKDOWN_KEY, md);
        toast.success(
          findings.length > 1
            ? `Full report generated (${findings.length} findings)`
            : "VAPT finding generated successfully",
        );
        return result;
      } catch (err) {
        const message =
          err instanceof ReportApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : "Failed to generate report";
        setError(message);
        toast.error(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  const generate = useCallback(
    async (payload: GenerateReportRequest) => {
      const findings =
        payload.findings ??
        (payload.finding ? [payload.finding as Finding] : []);
      return generateFromFindings(payload.target, findings as Finding[]);
    },
    [generateFromFindings],
  );

  const updateMarkdown = useCallback((value: string) => {
    setMarkdown(value);
    localStorage.setItem(MARKDOWN_KEY, value);
  }, []);

  const clearReport = useCallback(() => {
    setReport(null);
    setMarkdown("");
    setError(null);
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(MARKDOWN_KEY);
  }, []);

  return {
    report,
    markdown,
    isLoading,
    error,
    generate,
    generateFromFindings,
    updateMarkdown,
    clearReport,
  };
}
