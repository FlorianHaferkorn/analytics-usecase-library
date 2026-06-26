import { streamText } from 'ai';
import { resolveServerModel } from '@/lib/ai/orchestrator';
import { extractUsage, safeRecordAiStep } from '@/lib/ai/telemetry';
import { DISCOVERY_SYSTEM_PROMPT } from '@/lib/ai/prompts/discovery';
import { discoveryTools } from '@/lib/ai/tools/discovery-tools';
import { requireAuth } from '@/lib/auth/session';
import { buildEntityContext } from '@/lib/ai/context-builder';
import type { EntityContext } from '@/lib/ai/context-builder';

export async function POST(request: Request) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const body = await request.json();
  const { messages, context, entityContext } = body as {
    messages: Array<{ role: 'user' | 'assistant'; content: string }>;
    context?: string;
    entityContext?: EntityContext;
  };

  const resolved = await resolveServerModel('source-discovery');
  if (!resolved) {
    return new Response(
      JSON.stringify({ error: 'No LLM provider configured. Set GOOGLE_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY in .env.' }),
      { status: 503, headers: { 'Content-Type': 'application/json' } },
    );
  }
  const { model, choice } = resolved;
  const startedAt = Date.now();

  let systemPrompt = DISCOVERY_SYSTEM_PROMPT;

  // Inject entity context if provided
  if (entityContext && entityContext.entityType !== 'general') {
    try {
      const entityCtxStr = await buildEntityContext(entityContext);
      if (entityCtxStr) {
        systemPrompt = `${DISCOVERY_SYSTEM_PROMPT}\n\n## Entity Context\n\n${entityCtxStr}`;
      }
    } catch {
      // Fall back to base prompt silently
    }
  }

  // Existing context string still works (from AiField / DiscoveryChat)
  if (context) {
    systemPrompt = `${systemPrompt}\n\n## Source Context\n\n${context}`;
  }

  try {
    const result = streamText({
      model,
      system: systemPrompt,
      messages,
      tools: discoveryTools,
      onFinish: ({ usage }) => {
        safeRecordAiStep({
          taskRole: 'source-discovery', capabilityRole: choice.capabilityRole,
          provider: choice.provider, model: choice.modelId,
          usage: extractUsage(usage), latencyMs: Date.now() - startedAt, ok: true, rawUsage: usage,
        });
      },
    });

    return result.toTextStreamResponse();
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return new Response(
      JSON.stringify({ error: `LLM error: ${message}` }),
      { status: 500, headers: { 'Content-Type': 'application/json' } },
    );
  }
}
