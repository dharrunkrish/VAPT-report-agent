import { SEVERITY_OPTIONS, countBySeverity, severityBadgeClass } from "@/lib/severity";
import type { Finding } from "@/store/findingsStore";
import { cn } from "@/lib/utils";

interface SeveritySummaryBarProps {
  findings: Finding[];
  className?: string;
}

export function SeveritySummaryBar({ findings, className }: SeveritySummaryBarProps) {
  const counts = countBySeverity(findings);

  return (
    <div className={cn("flex flex-wrap items-center gap-3 text-xs font-mono", className)}>
      {SEVERITY_OPTIONS.map((sev) => (
        <span key={sev} className="inline-flex items-center gap-1.5">
          <span
            className={cn(
              "inline-block h-2 w-2 rounded-full border",
              severityBadgeClass(sev).replace("text-white", "").replace("text-black", ""),
            )}
          />
          {sev}: {counts[sev]}
        </span>
      ))}
      <span className="text-muted-foreground">
        · {findings.length} finding{findings.length === 1 ? "" : "s"} loaded
      </span>
    </div>
  );
}
