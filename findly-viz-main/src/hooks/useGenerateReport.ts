import { useCallback, useState } from "react";
import { toast } from "sonner";

import {
  generateFullReport,
  reportToMarkdownText,
  type GenerateReportRequest,
  type GenerateReportResponse,
  ReportApiError,
} from "@/services/reportApi";

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

  const generate = useCallback(async (payload: GenerateReportRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const finding = payload.finding ?? {
        endpoint: "",
        observation: "",
        evidence: "",
        notes: payload.findings?.[0]?.notes,
        request_evidence: payload.findings?.[0]?.request_evidence,
        ...payload.findings?.[0],
      };

      const result = await generateFullReport({
        target: payload.target,
        findings: [finding],
        section_prefix: payload.section_prefix,
      });

      const md = result.markdown || reportToMarkdownText(result);
      setReport(result);
      setMarkdown(md);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(result));
      localStorage.setItem(MARKDOWN_KEY, md);
      toast.success("VAPT finding generated successfully");
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
  }, []);

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
    updateMarkdown,
    clearReport,
  };
}
