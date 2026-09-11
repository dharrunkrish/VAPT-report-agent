import { createFileRoute } from "@tanstack/react-router";
import { createOpenAICompatible } from "@ai-sdk/openai-compatible";

const ASSIST_SYSTEM = `You are an assistant that MUST return ONLY a single raw JSON object (no markdown, no code fences, no explanation) matching this schema: { id, title, severity, owasp, wstg, endpoint, observation, evidence, steps_to_reproduce (array), notes, remediation (array), request_evidence }.
When asked to autofill, infer missing fields intelligently. When asked to update a single field, return the full JSON object with that field updated and other fields preserved. Do not fabricate unrelated content.`;

function extractJson(text: string): string | null {
  const start = text.indexOf("{");
  if (start === -1) return null;
  let depth = 0;
  for (let i = start; i < text.length; i++) {
    const ch = text[i];
    if (ch === "{") depth++;
    else if (ch === "}") depth--;
    if (depth === 0) return text.slice(start, i + 1);
  }
  return null;
}

function isValidFinding(f: any) {
  if (!f || typeof f !== "object") return false;
  if (!f.title || typeof f.title !== "string") return false;
  if (!f.observation || typeof f.observation !== "string") return false;
  if (f.steps_to_reproduce && !Array.isArray(f.steps_to_reproduce)) return false;
  if (f.remediation && !Array.isArray(f.remediation)) return false;
  return true;
}

export const Route = createFileRoute("/api/assist")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        try {
          const body = await request.json();
          const finding = body.finding || {};
          const mode = body.mode || "autofill"; // 'autofill' or 'field'
          const field = body.field;

          const apiKey = process.env.GROQ_API_KEY;
          if (!apiKey) return new Response("GROQ_API_KEY not configured", { status: 500 });

          const groqModel = process.env.GROQ_MODEL || "openai/gpt-oss-120b";
          const baseURL = "https://api.groq.com/openai/v1";

          const provider = createOpenAICompatible({ name: "groq", apiKey, baseURL });

          // Build user prompt
          let userPrompt = "";
          if (mode === "field" && field) {
            userPrompt = `Update this finding field \"${field}\". Current data:\n${JSON.stringify(finding, null, 2)}\nReturn ONLY the full JSON object with the updated field.`;
          } else {
            userPrompt = `Given this partial VAPT finding data, infer and fill ALL missing fields. Return ONLY valid JSON with keys: id, title, severity, owasp, wstg, endpoint, observation, evidence, steps_to_reproduce (array), notes, remediation (array), request_evidence.\nCurrent data:\n${JSON.stringify(finding, null, 2)}`;
          }

          // Try up to 2 attempts to get valid JSON
          for (let attempt = 0; attempt < 2; attempt++) {
            // Call the provider REST chat completions endpoint (non-stream) for reliable full text
            const resp = await fetch(`${baseURL}/chat/completions`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${apiKey}`,
              },
              body: JSON.stringify({ model: groqModel, messages: [{ role: "system", content: ASSIST_SYSTEM }, { role: "user", content: userPrompt }], stream: false }),
            });

            if (!resp.ok) {
              const errText = await resp.text();
              return new Response(`Model request failed: ${errText}`, { status: resp.status });
            }

            const json = await resp.json();
            // Try common places for the response text
            let text = "";
            if (json.choices && json.choices[0]) {
              const choice = json.choices[0];
              if (choice.message && typeof choice.message.content === "string") text = choice.message.content;
              else if (typeof choice.text === "string") text = choice.text;
              else if (choice.delta && typeof choice.delta === "string") text = choice.delta;
            } else if (typeof json.output === "string") {
              text = json.output;
            } else if (Array.isArray(json.output) && json.output[0] && json.output[0].content) {
              text = String(json.output[0].content);
            }

            const jsonText = extractJson(text || "");
            if (!jsonText) {
              // on first failure, append a clarification and retry
              if (attempt === 0) {
                userPrompt = `Your previous response was not valid JSON. Please return ONLY a single valid JSON object exactly matching the schema and nothing else. Current data:\n${JSON.stringify(finding, null, 2)}`;
                continue;
              }
              return new Response("AI did not return JSON", { status: 502 });
            }

            try {
              const parsed = JSON.parse(jsonText);
              if (!isValidFinding(parsed)) {
                if (attempt === 0) {
                  userPrompt = `Your previous JSON did not match the expected schema exactly. Please return ONLY a single valid JSON object with keys: id, title, severity, owasp, wstg, endpoint, observation, evidence, steps_to_reproduce (array), notes, remediation (array), request_evidence.`;
                  continue;
                }
                return new Response("AI returned JSON but it did not validate against the expected schema", { status: 502 });
              }

              return new Response(JSON.stringify(parsed), { status: 200, headers: { "Content-Type": "application/json" } });
            } catch (err) {
              if (attempt === 0) {
                userPrompt = `Your previous output could not be parsed as JSON. Please return ONLY a single valid JSON object matching the expected schema.`;
                continue;
              }
              return new Response("AI returned malformed JSON", { status: 502 });
            }
          }

          return new Response("Failed to obtain valid JSON from model", { status: 502 });
        } catch (err: any) {
          console.error("/api/assist error:", err);
          return new Response(String(err?.message ?? err ?? "unknown"), { status: 500 });
        }
      },
    },
  },
});
