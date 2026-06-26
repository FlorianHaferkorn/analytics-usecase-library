import { generateText } from 'ai';
import { resolveServerModel } from '@/lib/ai/orchestrator';
import { extractUsage, safeRecordAiStep } from '@/lib/ai/telemetry';
import {
  KPI_SYSTEM_PROMPT,
  BRACKET_SYSTEM_PROMPT,
  ACTION_SYSTEM_PROMPT,
  SOURCE_SYSTEM_PROMPT,
} from '@/lib/ai/prompts/wizard';
import { requireAuth } from '@/lib/auth/session';

const SYSTEM_PROMPTS: Record<string, string> = {
  kpi: KPI_SYSTEM_PROMPT,
  bracket: BRACKET_SYSTEM_PROMPT,
  action: ACTION_SYSTEM_PROMPT,
  source: SOURCE_SYSTEM_PROMPT,
};

/** wizard kind → AI config task-role (I-6.6 routing). */
const KIND_TASK_ROLE: Record<string, string> = {
  kpi: 'kpi-draft',
  bracket: 'bracket-synthesis',
  action: 'action-draft',
  source: 'source-discovery',
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

  const taskRole = KIND_TASK_ROLE[kind] ?? 'default';
  const resolved = await resolveServerModel(taskRole);
  if (!resolved) {
    return Response.json(
      { error: 'No LLM provider configured. Set GOOGLE_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY.' },
      { status: 503 },
    );
  }
  const { model, choice } = resolved;
  const startedAt = Date.now();

  try {
    const result = await generateText({
      model,
      system: systemPrompt,
      prompt: prompt || `Create a ${kind} for general business use.`,
      maxOutputTokens: 512,
    });

    safeRecordAiStep({
      taskRole, capabilityRole: choice.capabilityRole, provider: choice.provider, model: choice.modelId,
      usage: extractUsage(result.usage), latencyMs: Date.now() - startedAt, ok: true, rawUsage: result.usage,
    });

    const draft = JSON.parse(result.text.trim()) as Record<string, unknown>;
    return Response.json({ draft });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    safeRecordAiStep({
      taskRole, capabilityRole: choice.capabilityRole, provider: choice.provider, model: choice.modelId,
      usage: extractUsage(undefined), latencyMs: Date.now() - startedAt, ok: false, error: message,
    });
    return Response.json({ error: `AI generation failed: ${message}` }, { status: 500 });
  }
}
