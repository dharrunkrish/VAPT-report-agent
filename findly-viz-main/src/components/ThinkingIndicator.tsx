"use client";

import { cn } from "@/lib/utils";
import { motion } from "motion/react";
import { useEffect, useState } from "react";

import { Shimmer } from "@/components/ai-elements/shimmer";

type Phase = "analyzing" | "generating";

interface ThinkingIndicatorProps {
  isActive: boolean;
  variant?: "card" | "bubble";
  className?: string;
}

export function ThinkingIndicator({
  isActive,
  variant = "card",
  className,
}: ThinkingIndicatorProps) {
  const [phase, setPhase] = useState<Phase>("analyzing");

  useEffect(() => {
    if (!isActive) {
      setPhase("analyzing");
      return;
    }
    setPhase("analyzing");
    const timer = window.setTimeout(() => setPhase("generating"), 2000);
    return () => window.clearTimeout(timer);
  }, [isActive]);

  if (!isActive) return null;

  const label =
    phase === "analyzing"
      ? "🧠 Analyzing vulnerability..."
      : "📝 Generating report...";

  if (variant === "bubble") {
    return (
      <div className={cn("px-2 pt-1", className)}>
        <div className="inline-flex max-w-[85%] items-center gap-2 rounded-2xl border border-border/60 bg-muted/40 px-4 py-3">
          <TypingDots />
          <Shimmer className="text-sm text-muted-foreground">{label}</Shimmer>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      animate={{ opacity: [0.72, 1, 0.72] }}
      className={cn(
        "rounded-xl border border-border/60 bg-muted/30 px-4 py-6 text-center",
        className,
      )}
      transition={{ duration: 1.6, repeat: Number.POSITIVE_INFINITY }}
    >
      <Shimmer className="text-sm font-medium">{label}</Shimmer>
      <p className="mt-2 text-xs font-mono text-muted-foreground">
        analysis → severity → report writer
      </p>
      <div className="mx-auto mt-4 h-2 w-48 overflow-hidden rounded-full bg-muted">
        <motion.div
          animate={{ x: ["-100%", "100%"] }}
          className="h-full w-1/2 bg-primary/40"
          transition={{ duration: 1.2, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
        />
      </div>
    </motion.div>
  );
}

function TypingDots() {
  return (
    <div className="flex items-center gap-1" aria-hidden>
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          animate={{ opacity: [0.25, 1, 0.25], y: [0, -2, 0] }}
          className="h-2 w-2 rounded-full bg-primary/70"
          transition={{
            duration: 0.9,
            repeat: Number.POSITIVE_INFINITY,
            delay: i * 0.15,
          }}
        />
      ))}
    </div>
  );
}
