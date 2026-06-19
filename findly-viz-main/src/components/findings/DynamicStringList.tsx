import { Plus, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface DynamicStringListProps {
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
  addLabel: string;
  placeholder?: string;
  disabled?: boolean;
}

export function DynamicStringList({
  label,
  values,
  onChange,
  addLabel,
  placeholder,
  disabled,
}: DynamicStringListProps) {
  const rows = values.length > 0 ? values : [""];

  const updateRow = (index: number, value: string) => {
    const next = [...rows];
    next[index] = value;
    onChange(next);
  };

  const removeRow = (index: number) => {
    if (rows.length <= 1) {
      onChange([""]);
      return;
    }
    onChange(rows.filter((_, i) => i !== index));
  };

  const addRow = () => onChange([...rows, ""]);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium leading-none">{label}</span>
        <Button type="button" variant="outline" size="sm" onClick={addRow} disabled={disabled}>
          <Plus className="mr-1 h-3.5 w-3.5" />
          {addLabel}
        </Button>
      </div>
      <div className="space-y-2">
        {rows.map((value, index) => (
          <div key={index} className="flex items-start gap-2">
            <span className="mt-2 w-6 shrink-0 text-xs font-mono text-muted-foreground">
              {index + 1}.
            </span>
            <Input
              value={value}
              onChange={(e) => updateRow(index, e.target.value)}
              placeholder={placeholder}
              disabled={disabled}
              className="flex-1"
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="shrink-0 text-muted-foreground hover:text-destructive"
              onClick={() => removeRow(index)}
              disabled={disabled}
              aria-label={`Remove ${label} ${index + 1}`}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
