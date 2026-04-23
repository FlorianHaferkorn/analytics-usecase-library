import { streamText } from 'ai';
import { createServerModel } from '@/lib/ai/orchestrator';
import { DISCOVERY_SYSTEM_PROMPT } from '@/lib/ai/prompts/discovery';
import { discoveryTools } from '@/lib/ai/tools/discovery-tools';
import { requireAuth } from '@/lib/auth/session';

export async function POST(request: Request) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const body = await request.json();
  const { messages, context } = body as {
    messages: Array<{ role: 'user' | 'assistant'; content: string }>;
    context?: string;
  };

  const model = await createServerModel();
  if (!model) {
    return new Response(
      JSON.stringify({ error: 'No LLM provider configured. Set GOOGLE_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY in .env.' }),
      { status: 503, headers: { 'Content-Type': 'application/json' } },
    );
  }

  const systemPrompt = context
    ? `${DISCOVERY_SYSTEM_PROMPT}\n\n## Source Context\n\n${context}`
    : DISCOVERY_SYSTEM_PROMPT;

  try {
    const result = streamText({
      model,
      system: systemPrompt,
      messages,
      tools: discoveryTools,
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
