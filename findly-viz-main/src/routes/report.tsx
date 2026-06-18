import { createFileRoute } from "@tanstack/react-router";

import { ReportGenerator } from "@/pages/ReportGenerator";

export const Route = createFileRoute("/report")({
  head: () => ({
    meta: [
      { title: "VAPT Report Generator" },
      {
        name: "description",
        content: "Generate professional VAPT findings with AI-powered report generation.",
      },
    ],
  }),
  component: ReportGenerator,
});
