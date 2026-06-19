import { createFileRoute } from "@tanstack/react-router";

import { FindingsManager } from "@/pages/FindingsManager";

export const Route = createFileRoute("/findings-manager")({
  head: () => ({
    meta: [
      { title: "Findings Manager" },
      {
        name: "description",
        content: "Manage, edit, and export VAPT findings before report generation.",
      },
    ],
  }),
  component: FindingsManager,
});
