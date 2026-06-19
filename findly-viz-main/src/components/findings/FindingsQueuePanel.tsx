import { Plus, Trash2 } from "lucide-react";

import { SeverityBadge } from "@/components/findings/SeverityBadge";
import { SeveritySummaryBar } from "@/components/findings/SeveritySummaryBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Finding } from "@/store/findingsStore";

interface FindingsQueuePanelProps {
  findings: Finding[];
  onRemove: (index: number) => void;
  onAddAnother: () => void;
}

export function FindingsQueuePanel({
  findings,
  onRemove,
  onAddAnother,
}: FindingsQueuePanelProps) {
  if (findings.length === 0) return null;

  return (
    <Card className="border-border/60">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle className="text-base">Findings Queue</CardTitle>
          <Button type="button" variant="outline" size="sm" onClick={onAddAnother}>
            <Plus className="mr-1.5 h-3.5 w-3.5" />
            Add Another
          </Button>
        </div>
        <SeveritySummaryBar findings={findings} className="mt-2" />
      </CardHeader>
      <CardContent className="space-y-2">
        {findings.map((finding, index) => (
          <div
            key={`${finding.id ?? finding.title}-${index}`}
            className="flex items-start justify-between gap-3 rounded-md border bg-background p-3"
          >
            <div className="min-w-0 space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <SeverityBadge severity={finding.severity} />
                {finding.id && (
                  <span className="font-mono text-[10px] text-muted-foreground">{finding.id}</span>
                )}
              </div>
              <p className="truncate text-sm font-medium">{finding.title || "Untitled Finding"}</p>
              {finding.endpoint && (
                <p className="truncate font-mono text-[11px] text-muted-foreground">
                  {finding.endpoint}
                </p>
              )}
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="shrink-0 text-muted-foreground hover:text-destructive"
              onClick={() => onRemove(index)}
              aria-label="Remove finding"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
