export type LlmProvider = "gemini" | "azure" | "openai" | "none";

export interface LlmMessage {
  role: "user" | "assistant";
  content: string;
}

export interface LlmRequest {
  messages: LlmMessage[];
  system?: string;
  max_tokens?: number;
}

/** Detects which LLM provider is configured (server-side only). */
export function detectProvider(): LlmProvider {
  if (process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY) return "gemini";
  if (process.env.AZURE_OPENAI_API_KEY) return "azure";
  if (process.env.OPENAI_API_KEY) return "openai";
  return "none";
}

/** Call the configured LLM provider and return the assistant reply. Server-side only. */
export async function callLlm(req: LlmRequest): Promise<string> {
  const provider = detectProvider();

  if (provider === "gemini") return callGemini(req);
  if (provider === "azure") return callAzure(req);
  if (provider === "openai") return callOpenAi(req);

  return "⚠️ No LLM provider configured. Add GEMINI_API_KEY, OPENAI_API_KEY, or Azure credentials to .env and restart.";
}

async function callGemini(req: LlmRequest): Promise<string> {
  const apiKey = process.env.GEMINI_API_KEY ?? process.env.GOOGLE_API_KEY!;
  const model = process.env.GEMINI_MODEL ?? "gemini-2.5-flash";
  const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;

  const contents = req.messages.map((m) => ({
    role: m.role === "assistant" ? "model" : "user",
    parts: [{ text: m.content }],
  }));

  const body: Record<string, unknown> = { contents };
  if (req.system) {
    body.systemInstruction = { parts: [{ text: req.system }] };
  }

  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Gemini error ${res.status}: ${await res.text()}`);
  const data = await res.json();
  return data.candidates?.[0]?.content?.parts?.[0]?.text ?? "(no response)";
}

async function callAzure(req: LlmRequest): Promise<string> {
  const key = process.env.AZURE_OPENAI_API_KEY!;
  const endpoint = process.env.AZURE_OPENAI_ENDPOINT!;
  const deployment = process.env.AZURE_OPENAI_DEPLOYMENT!;
  const url = `${endpoint}/openai/deployments/${deployment}/chat/completions?api-version=2024-02-01`;

  const messages = req.system
    ? [{ role: "system", content: req.system }, ...req.messages]
    : req.messages;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", "api-key": key },
    body: JSON.stringify({ messages, max_tokens: req.max_tokens ?? 2048 }),
  });
  if (!res.ok) throw new Error(`Azure error ${res.status}: ${await res.text()}`);
  const data = await res.json();
  return data.choices?.[0]?.message?.content ?? "(no response)";
}

async function callOpenAi(req: LlmRequest): Promise<string> {
  const key = process.env.OPENAI_API_KEY!;
  const model = process.env.OPENAI_MODEL ?? "gpt-4o-mini";

  const messages = req.system
    ? [{ role: "system", content: req.system }, ...req.messages]
    : req.messages;

  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${key}` },
    body: JSON.stringify({ model, messages, max_tokens: req.max_tokens ?? 2048 }),
  });
  if (!res.ok) throw new Error(`OpenAI error ${res.status}: ${await res.text()}`);
  const data = await res.json();
  return data.choices?.[0]?.message?.content ?? "(no response)";
}
