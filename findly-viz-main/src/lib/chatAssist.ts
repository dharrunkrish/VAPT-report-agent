/** Call the streaming chat API and collect the full text response. */
export async function requestChatCompletion(userText: string): Promise<string> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: [
        {
          id: crypto.randomUUID(),
          role: "user",
          parts: [{ type: "text", text: userText }],
        },
      ],
    }),
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response stream");

  const decoder = new TextDecoder();
  let buffer = "";
  let text = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      // AI SDK UI message stream: text deltas often appear as JSON chunks
      if (trimmed.startsWith("0:")) {
        try {
          const parsed = JSON.parse(trimmed.slice(2));
          if (typeof parsed === "string") text += parsed;
        } catch {
          /* ignore */
        }
      } else if (trimmed.includes('"type":"text-delta"') || trimmed.includes('"type": "text-delta"')) {
        try {
          const jsonStart = trimmed.indexOf("{");
          if (jsonStart >= 0) {
            const chunk = JSON.parse(trimmed.slice(jsonStart));
            if (chunk.delta) text += chunk.delta;
            if (chunk.textDelta) text += chunk.textDelta;
          }
        } catch {
          /* ignore */
        }
      } else if (trimmed.startsWith("data:")) {
        const payload = trimmed.slice(5).trim();
        if (payload === "[DONE]") continue;
        try {
          const chunk = JSON.parse(payload);
          if (typeof chunk === "string") text += chunk;
          if (chunk.type === "text-delta" && chunk.delta) text += chunk.delta;
        } catch {
          /* ignore */
        }
      }
    }
  }

  return text.trim();
}
