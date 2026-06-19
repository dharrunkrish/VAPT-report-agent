import { cn } from "@/lib/utils";
import { normalizeSeverity, severityBadgeClass } from "@/lib/severity";
import type { Severity } from "@/store/findingsStore";

interface SeverityBadgeProps {
  severity: Severity | string;
  className?: string;
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  const normalized = normalizeSeverity(severity);
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-bold tracking-wide",
        severityBadgeClass(normalized),
        className,
      )}
    >
      {normalized}
    </span>
  );
}
