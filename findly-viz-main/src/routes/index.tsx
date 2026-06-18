import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useEffect, useRef, useState } from "react";
import { ShieldCheck, Sparkles, Trash2 } from "lucide-react";
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
import { ProtectedMessageResponse } from "@/components/ProtectedMessageResponse";
import { ThinkingIndicator } from "@/components/ThinkingIndicator";
import { Button } from "@/components/ui/button";
import { getMessageText, parseReportMarkdown } from "@/lib/parseReportMarkdown";
import { setTransferPayload } from "@/stores/reportTransferStore";

const STORAGE_KEY = "vapt-chat-messages-v1";

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
  const { messages, sendMessage, status, setMessages, stop } = useChat({
    messages: initial,
    transport: new DefaultChatTransport({ api: "/api/chat" }),
  });

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch {
      /* ignore */
    }
  }, [messages]);

  useEffect(() => {
    if (status === "ready") textareaRef.current?.focus();
  }, [status]);

  const handleSubmit = (msg: PromptInputMessage) => {
    if (!msg.text?.trim()) return;
    sendMessage({ text: msg.text });
  };

  const handleClear = () => {
    setMessages([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
    textareaRef.current?.focus();
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
    setTransferPayload(parsed);
    toast.success("Finding transferred to Report Generator");
    navigate({ to: "/report" });
  };

  const isBusy = status === "submitted" || status === "streaming";
  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
  const lastAssistantId = lastAssistant?.id;
  const lastAssistantText = lastAssistant ? getMessageText(lastAssistant) : "";
  const showThinking =
    isBusy && (status === "submitted" || !lastAssistantText.trim());

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
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClear}
              disabled={messages.length === 0 || isBusy}
              className="text-muted-foreground hover:text-foreground"
            >
              <Trash2 className="mr-1.5 h-3.5 w-3.5" />
              New
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-4">
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
                        {isCompleteAssistant && text.trim() && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleTransfer(m)}
                          >
                            📋 Transfer to Report
                          </Button>
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
