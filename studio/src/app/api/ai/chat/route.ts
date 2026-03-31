import { streamText } from 'ai';
import { createModel, detectProvider } from '@/lib/ai/orchestrator';
import { DISCOVERY_SYSTEM_PROMPT } from '@/lib/ai/prompts/discovery';
import { discoveryTools } from '@/lib/ai/tools/discovery-tools';

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
    tools: discoveryTools,
  });

  return result.toTextStreamResponse();
}
