"use client";

import type { ComponentProps } from "react";
import { toast } from "sonner";

import { MessageResponse } from "@/components/ai-elements/message";
import { cn } from "@/lib/utils";

type ProtectedMessageResponseProps = ComponentProps<typeof MessageResponse>;

export function ProtectedMessageResponse({
  className,
  onContextMenu,
  ...props
}: ProtectedMessageResponseProps) {
  const handleContextMenu = (event: React.MouseEvent<HTMLDivElement>) => {
    event.preventDefault();
    toast.message("Use the Transfer to Report button instead of copying from chat.");
    onContextMenu?.(event);
  };

  return (
    <div
      className={cn("select-none", className)}
      onContextMenu={handleContextMenu}
      title="Use Transfer to Report for structured export"
    >
      <MessageResponse {...props} />
    </div>
  );
}
