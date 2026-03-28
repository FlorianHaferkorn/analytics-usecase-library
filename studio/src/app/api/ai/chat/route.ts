import { streamText } from 'ai';
import { createModel, detectProvider } from '@/lib/ai/orchestrator';
import { DISCOVERY_SYSTEM_PROMPT } from '@/lib/ai/prompts/discovery';

export async function POST(request: Request) {
  const body = await request.json();
  const { messages, apiKey, context } = body as {
    messages: Array<{ role: 'user' | 'assistant'; content: string }>;
    apiKey: string;
    context?: string;
  };

  if (!apiKey) {
    return new Response(JSON.stringify({ error: 'API key required (BYOK)' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const provider = detectProvider(apiKey);
  const model = createModel({ provider, apiKey });

  const systemPrompt = context
    ? `${DISCOVERY_SYSTEM_PROMPT}\n\n## Source Context\n\n${context}`
    : DISCOVERY_SYSTEM_PROMPT;

  const result = streamText({
    model,
    system: systemPrompt,
    messages,
  });

  return result.toTextStreamResponse();
}
