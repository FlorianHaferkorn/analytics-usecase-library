import { generateText } from 'ai';
import { createServerModel } from '@/lib/ai/orchestrator';
import { KPI_SYSTEM_PROMPT, BRACKET_SYSTEM_PROMPT, ACTION_SYSTEM_PROMPT } from '@/lib/ai/prompts/wizard';
import { requireAuth } from '@/lib/auth/session';

const SYSTEM_PROMPTS: Record<string, string> = {
  kpi: KPI_SYSTEM_PROMPT,
  bracket: BRACKET_SYSTEM_PROMPT,
  action: ACTION_SYSTEM_PROMPT,
};

export async function POST(request: Request) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const body = await request.json() as { kind?: string; prompt?: string };
  const { kind = 'kpi', prompt = '' } = body;

  const systemPrompt = SYSTEM_PROMPTS[kind];
  if (!systemPrompt) {
    return Response.json({ error: `Unknown kind: ${kind}` }, { status: 400 });
  }

  const model = await createServerModel();
  if (!model) {
    return Response.json(
      { error: 'No LLM provider configured. Set GOOGLE_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY.' },
      { status: 503 },
    );
  }

  try {
    const { text } = await generateText({
      model,
      system: systemPrompt,
      prompt: prompt || `Create a ${kind} for general business use.`,
      maxOutputTokens: 512,
    });

    const draft = JSON.parse(text.trim()) as Record<string, unknown>;
    return Response.json({ draft });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return Response.json({ error: `AI generation failed: ${message}` }, { status: 500 });
  }
}
