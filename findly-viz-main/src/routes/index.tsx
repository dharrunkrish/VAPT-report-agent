import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, ChevronUp, ShieldCheck, Sparkles, Trash2, X } from "lucide-react";
import { toast } from "sonner";

import logo from "@/assets/vapt-logo.png";
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import { Message, MessageContent } from "@/components/ai-elements/message";
import {
  PromptInput,
  PromptInputTextarea,
  PromptInputFooter,
  PromptInputSubmit,
  type PromptInputMessage,
} from "@/components/ai-elements/prompt-input";
import { SeverityBadge } from "@/components/findings/SeverityBadge";
import { ProtectedMessageResponse } from "@/components/ProtectedMessageResponse";
import { ThinkingIndicator } from "@/components/ThinkingIndicator";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getMessageText, parseReportMarkdown } from "@/lib/parseReportMarkdown";
import { useFindingsStore } from "@/store/findingsStore";

const STORAGE_KEY = "vapt-chat-messages-v1";
const VERSIONS_KEY = "vapt-chat-report-versions-v1";
const ACTIVE_FINDING_KEY = "vapt-chat-active-finding-v1";

const SAMPLE_INPUT = `{
  "target": "https://staging.acme-corp.com",
  "finding": {
    "endpoint": "/api/v2/users/{id}",
    "observation": "IDOR — authenticated user can read any other user's profile by changing the {id} path parameter.",
    "evidence": "Sending GET /api/v2/users/1042 while logged in as user 9001 returned the full profile of user 1042, including email and phone.",
    "notes": "No authorization check tying the requested id to the session subject. Affects all v2 user endpoints.",
    "request_evidence": "GET /api/v2/users/1042 HTTP/1.1\\nHost: staging.acme-corp.com\\nAuthorization: Bearer eyJhbGciOi...\\nAccept: application/json"
  }
}`;

const QUICK_ACTIONS = [
  { label: "🔴 Change Severity", message: "Change the severity in the last report. Output the complete updated report." },
  { label: "📝 Rewrite Description", message: "Rewrite the Description section to be more technical and precise. Output the complete updated report." },
  { label: "🔧 Add Remediation Step", message: "Add one more specific remediation recommendation. Output the complete updated report." },
  { label: "📋 Add Step to Reproduce", message: "Add one more step to reproduce. Output the complete updated report." },
  { label: "✏️ Make More Formal", message: "Make the entire report more formal and enterprise-ready. Output the complete updated report." },
  { label: "🔁 Regenerate", message: "Regenerate the full report from scratch using the same finding data. Output the complete updated report." },
] as const;

interface ReportVersion {
  id: string;
  text: string;
  timestamp: string;
}

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "VAPT Reporting Assistant" },
      {
        name: "description",
        content:
          "Turn raw security findings into clean, structured VAPT reports in seconds.",
      },
      { property: "og:title", content: "VAPT Reporting Assistant" },
      {
        property: "og:description",
        content:
          "Turn raw security findings into clean, structured VAPT reports in seconds.",
      },
    ],
  }),
  component: Index,
});

function Index() {
  const [hydrated, setHydrated] = useState(false);
  const [initialMessages, setInitialMessages] = useState<any[]>([]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setInitialMessages(JSON.parse(raw));
    } catch {
      /* ignore */
    }
    setHydrated(true);
  }, []);

  if (!hydrated) return null;
  return <Chat initial={initialMessages} />;
}

function Chat({ initial }: { initial: any[] }) {
  const navigate = useNavigate();
  const importFindings = useFindingsStore((s) => s.importFindings);
  const { messages, sendMessage, status, setMessages, stop } = useChat({
    messages: initial,
    transport: new DefaultChatTransport({ api: "/api/chat" }),
  });

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [versions, setVersions] = useState<ReportVersion[]>(() => {
    try {
      const raw = localStorage.getItem(VERSIONS_KEY);
      return raw ? (JSON.parse(raw) as ReportVersion[]) : [];
    } catch {
      return [];
    }
  });
  const [showVersions, setShowVersions] = useState(false);
  const [activeFinding, setActiveFinding] = useState<ReturnType<typeof parseReportMarkdown> | null>(() => {
    try {
      const raw = localStorage.getItem(ACTIVE_FINDING_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });
  const savedVersionIds = useRef(new Set<string>());

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch {
      /* ignore */
    }
  }, [messages]);

  useEffect(() => {
    localStorage.setItem(VERSIONS_KEY, JSON.stringify(versions));
  }, [versions]);

  useEffect(() => {
    if (activeFinding) {
      localStorage.setItem(ACTIVE_FINDING_KEY, JSON.stringify(activeFinding));
    } else {
      localStorage.removeItem(ACTIVE_FINDING_KEY);
    }
  }, [activeFinding]);

  useEffect(() => {
    if (status === "ready") textareaRef.current?.focus();
  }, [status]);

  const handleSubmit = (msg: PromptInputMessage) => {
    if (!msg.text?.trim()) return;
    sendMessage({ text: msg.text });
  };

  const handleClear = () => {
    stop();
    setMessages([]);
    setActiveFinding(null);
    setVersions([]);
    savedVersionIds.current.clear();
    try {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(VERSIONS_KEY);
      localStorage.removeItem(ACTIVE_FINDING_KEY);
    } catch {
      /* ignore */
    }
    const ta = textareaRef.current;
    if (ta) {
      ta.value = "";
      ta.dispatchEvent(new Event("input", { bubbles: true }));
      ta.focus();
    }
  };

  const insertSample = () => {
    const ta = textareaRef.current;
    if (ta) {
      ta.value = SAMPLE_INPUT;
      ta.focus();
      ta.dispatchEvent(new Event("input", { bubbles: true }));
    }
  };

  const handleTransfer = (message: (typeof messages)[number]) => {
    const text = getMessageText(message);
    if (!text.trim()) {
      toast.error("No report content to transfer");
      return;
    }
    const parsed = parseReportMarkdown(text);
    importFindings(parsed.target, [parsed.finding]);
    sessionStorage.setItem("vapt-chat-transfer-v1", JSON.stringify(parsed));
    toast.success("Finding transferred to Findings Manager");
    navigate({ to: "/findings-manager" });
  };

  const sendQuickAction = (message: string) => {
    sendMessage({ text: message });
  };

  const isBusy = status === "submitted" || status === "streaming";
  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
  const lastAssistantId = lastAssistant?.id;
  const lastAssistantText = lastAssistant ? getMessageText(lastAssistant) : "";
  const showThinking =
    isBusy && (status === "submitted" || !lastAssistantText.trim());

  useEffect(() => {
    if (status !== "ready" || !lastAssistant?.id) return;
    const text = getMessageText(lastAssistant);
    if (!text.includes("VAPT Security Finding Report")) return;
    if (savedVersionIds.current.has(lastAssistant.id)) return;

    savedVersionIds.current.add(lastAssistant.id);
    const parsed = parseReportMarkdown(text);
    setActiveFinding(parsed);
    setVersions((prev) => [
      {
        id: lastAssistant.id,
        text,
        timestamp: new Date().toISOString(),
      },
      ...prev,
    ]);
  }, [status, lastAssistant]);

  const activeTitle = useMemo(
    () => activeFinding?.finding.title ?? "No active finding",
    [activeFinding],
  );

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-border/60 bg-background/70 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <img
              src={logo}
              alt="VAPT shield logo"
              width={36}
              height={36}
              className="h-9 w-9"
            />
            <div className="flex flex-col leading-tight">
              <h1 className="text-sm font-semibold tracking-tight text-foreground">
                VAPT Reporting Assistant
              </h1>
              <p className="text-xs text-muted-foreground font-mono">
                pentest_findings → structured_report
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild>
              <Link to="/report">Report</Link>
            </Button>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/findings-manager">Findings Manager</Link>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClear}
              disabled={messages.length === 0}
              className="text-muted-foreground hover:text-foreground"
            >
              <Trash2 className="mr-1.5 h-3.5 w-3.5" />
              New Chat
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-4">
        {activeFinding && (
          <Card className="mt-4 border-border/60">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 pt-4">
              <CardTitle className="text-sm">Active Finding</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setActiveFinding(null)}
                className="h-7 px-2 text-xs"
              >
                <X className="mr-1 h-3 w-3" />
                Clear Finding
              </Button>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center gap-2 pb-4 text-sm">
              <SeverityBadge severity={activeFinding.finding.severity} />
              <span className="font-medium">{activeTitle}</span>
            </CardContent>
          </Card>
        )}

        {versions.length > 0 && (
          <div className="mt-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowVersions((v) => !v)}
              className="w-full justify-between"
            >
              <span>📜 Version History ({versions.length})</span>
              {showVersions ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
            {showVersions && (
              <div className="mt-2 space-y-2">
                {versions.map((version) => (
                  <details
                    key={version.id}
                    className="rounded-md border bg-muted/20 px-3 py-2 text-xs"
                  >
                    <summary className="cursor-pointer font-mono text-muted-foreground">
                      {new Date(version.timestamp).toLocaleString()}
                    </summary>
                    <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap text-[11px]">
                      {version.text.slice(0, 1200)}
                      {version.text.length > 1200 ? "…" : ""}
                    </pre>
                  </details>
                ))}
              </div>
            )}
          </div>
        )}

        <Conversation className="flex-1">
          <ConversationContent className="px-0">
            {messages.length === 0 ? (
              <ConversationEmptyState
                icon={
                  <ShieldCheck className="h-10 w-10 text-primary" strokeWidth={1.5} />
                }
                title="Paste a finding to generate a report"
                description="Drop in raw JSON, scanner output, or a freeform description. I'll render a clean VAPT report in the standard layout."
              >
                <Button
                  variant="outline"
                  size="sm"
                  onClick={insertSample}
                  className="mt-4"
                >
                  <Sparkles className="mr-1.5 h-3.5 w-3.5" />
                  Try sample finding
                </Button>
              </ConversationEmptyState>
            ) : (
              messages.map((m) => {
                const isAssistant = m.role === "assistant";
                const isCompleteAssistant =
                  isAssistant && (!isBusy || m.id !== lastAssistantId);
                const text = getMessageText(m);
                const isReport = text.includes("VAPT Security Finding Report");

                return (
                  <Message from={m.role} key={m.id}>
                    {m.role === "user" ? (
                      <MessageContent>
                        <pre className="whitespace-pre-wrap break-words font-mono text-xs leading-relaxed">
                          {text}
                        </pre>
                      </MessageContent>
                    ) : (
                      <div className="w-full max-w-full space-y-3 overflow-x-auto">
                        {text.trim() ? (
                          <ProtectedMessageResponse>{text}</ProtectedMessageResponse>
                        ) : isBusy && m.id === lastAssistantId ? (
                          <ThinkingIndicator isActive variant="bubble" />
                        ) : null}
                        {isCompleteAssistant && isReport && text.trim() && (
                          <>
                            <div className="flex flex-wrap gap-2">
                              {QUICK_ACTIONS.map((action) => (
                                <Button
                                  key={action.label}
                                  variant="outline"
                                  size="sm"
                                  className="text-xs"
                                  disabled={isBusy}
                                  onClick={() => sendQuickAction(action.message)}
                                >
                                  {action.label}
                                </Button>
                              ))}
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleTransfer(m)}
                            >
                              📋 Transfer to Report
                            </Button>
                          </>
                        )}
                      </div>
                    )}
                  </Message>
                );
              })
            )}
            {showThinking && (
              <ThinkingIndicator isActive variant="bubble" />
            )}
          </ConversationContent>
          <ConversationScrollButton />
        </Conversation>

        <div className="sticky bottom-0 pb-4 pt-2 bg-gradient-to-t from-background via-background to-transparent">
          <PromptInput onSubmit={handleSubmit}>
            <PromptInputTextarea
              ref={textareaRef}
              placeholder="Paste a JSON finding, scanner output, or describe the vulnerability…"
              className="font-mono text-sm min-h-[80px]"
              disabled={isBusy}
            />
            <PromptInputFooter className="justify-between">
              <span className="text-[11px] text-muted-foreground font-mono px-1">
                ⏎ to send · ⇧⏎ for newline
              </span>
              <PromptInputSubmit
                status={status}
                disabled={isBusy ? false : undefined}
                onClick={isBusy ? (e) => { e.preventDefault(); stop(); } : undefined}
              />
            </PromptInputFooter>
          </PromptInput>
        </div>
      </main>
    </div>
  );
}
