import { NextRequest, NextResponse } from "next/server";
import { callLlm, detectProvider } from "@/lib/llm";

const SYSTEM_PROMPT = `You are the ActionReady Studio assistant — an expert in analytics strategy, KPI frameworks, and use case design.

Your role is to help users design Golden Thread use cases: linking business strategy to KPIs, influencing levers, and prescriptive action codes.

Key principles:
- The Golden Thread: Strategy → KPI (North Star) → Influencing KPIs → Action Codes
- The 3-30-300 rule: 3s (status), 30s (diagnosis), 300s (action)
- Every KPI must be causal, not just correlated
- Action Codes must be imperative and prescriptive (e.g. "Review top 10 customers by DSO > 45 days")
- Keep things lean: one strategic KPI per use case, 3-6 influencing KPIs

When suggesting KPI IDs, use the dot-notation format: domain.entity.metric (e.g. wc.dso.days, sales.net_sales.amount).
When suggesting action code IDs, use the format: Domain-Type#.# (e.g. F-C1.1, C-M2.1).

If the user provides source documents, ground your suggestions in those documents.`;

export async function POST(req: NextRequest) {
  try {
    const { messages, sources } = await req.json();

    // Build context from active sources
    const sourceContext =
      sources && sources.length > 0
        ? "\n\n---\nSOURCE DOCUMENTS:\n" +
          sources
            .filter((s: { include_in_chat: boolean }) => s.include_in_chat)
            .map((s: { name: string; content: string }) => `[${s.name}]\n${s.content.slice(0, 4000)}`)
            .join("\n\n---\n")
        : "";

    const systemWithContext = sourceContext
      ? SYSTEM_PROMPT + sourceContext
      : SYSTEM_PROMPT;

    const reply = await callLlm({
      messages,
      system: systemWithContext,
      max_tokens: 2048,
    });

    return NextResponse.json({ reply, provider: detectProvider() });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}

export async function GET() {
  return NextResponse.json({ provider: detectProvider() });
}
