import { Upload, X } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { parseFindingsJson } from "@/lib/findingsJson";
import { cn } from "@/lib/utils";
import type { Finding } from "@/store/findingsStore";

interface JsonUploadZoneProps {
  onImport: (target: string, findings: Finding[]) => void;
  className?: string;
}

export function JsonUploadZone({ onImport, className }: JsonUploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = async (file: File) => {
    if (!file.name.endsWith(".json")) {
      toast.error("Only .json files are supported");
      return;
    }
    try {
      const text = await file.text();
      const parsed = parseFindingsJson(JSON.parse(text));
      onImport(parsed.target, parsed.findings);
      setFilename(file.name);
      toast.success(`Loaded ${parsed.findings.length} finding(s)`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to parse JSON");
    }
  };

  const clearFile = () => {
    setFilename(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className={cn("space-y-2", className)}>
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const file = e.dataTransfer.files[0];
          if (file) void handleFile(file);
        }}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors",
          dragOver ? "border-primary bg-primary/5" : "border-border/60 hover:border-primary/50",
        )}
      >
        <Upload className="mb-2 h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium">Drop your findings JSON here or click to browse</p>
        <p className="mt-1 text-xs text-muted-foreground">Accepts .json only</p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".json,application/json"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void handleFile(file);
        }}
      />
      {filename && (
        <div className="flex items-center justify-between rounded-md border bg-muted/30 px-3 py-2 text-sm">
          <span className="truncate font-mono text-xs">{filename}</span>
          <Button type="button" variant="ghost" size="sm" onClick={clearFile}>
            <X className="mr-1 h-3.5 w-3.5" />
            Clear
          </Button>
        </div>
      )}
    </div>
  );
}
