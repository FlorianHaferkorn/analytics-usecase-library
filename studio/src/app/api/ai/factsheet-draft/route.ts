import { generateText } from 'ai';
import { createServerModel } from '@/lib/ai/orchestrator';
import { requireAuth } from '@/lib/auth/session';

const SYSTEM_PROMPT =
  'You are helping draft a new KPI or use case for an analytics governance library. ' +
  'Based on the user\'s description, suggest values for these fields: ' +
  'name (short, max 5 words), description (1-2 sentences), ' +
  'domain (one of: Commercial, Finance, Operations, SupplyChain, XD), ' +
  'type (one of: flow, stock, ratio, index), ' +
  'grain (e.g. "daily by product"), unit (e.g. "% or EUR"). ' +
  'Return ONLY a JSON object with keys: name, description, domain, type, grain, unit.';

interface FactsheetDraft {
  name: string;
  description: string;
  domain: string;
  type: string;
  grain: string;
  unit: string;
}

function fallbackFromPrompt(prompt: string): FactsheetDraft {
  const words = prompt.trim().split(/\s+/).slice(0, 5).join(' ');
  return {
    name: words || 'New Use Case',
    description: prompt.slice(0, 200) || 'A new analytics use case.',
    domain: 'Commercial',
    type: 'flow',
    grain: 'daily',
    unit: '',
  };
}

export async function POST(request: Request) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const body = await request.json() as { prompt?: string };
  const { prompt = '' } = body;

  const model = await createServerModel();
  if (!model) {
    return Response.json(fallbackFromPrompt(prompt));
  }

  try {
    const { text } = await generateText({
      model,
      system: SYSTEM_PROMPT,
      prompt: prompt || 'A general business analytics use case.',
      maxOutputTokens: 256,
    });

    const cleaned = text.trim().replace(/^```json\s*/i, '').replace(/\s*```$/i, '');
    const draft = JSON.parse(cleaned) as FactsheetDraft;
    return Response.json(draft);
  } catch {
    return Response.json(fallbackFromPrompt(prompt));
  }
}
