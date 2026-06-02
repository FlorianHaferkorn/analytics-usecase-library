import { generateText } from 'ai';
import { createServerModel } from '@/lib/ai/orchestrator';
import { requireAuth } from '@/lib/auth/session';
import {
  reconcileDeterministic,
  type ReconcileEditedSource,
} from '@/lib/studio/cascading-reconcile';

const DRAFT_SYSTEM_PROMPT =
  'You are helping draft a new KPI or use case for an analytics governance library. ' +
  "Based on the user's description, suggest values for these fields: " +
  'name (short, max 5 words), description (1-2 sentences), ' +
  'domain (one of: Commercial, Finance, Operations, SupplyChain, XD), ' +
  'type (one of: flow, stock, ratio, index), ' +
  'grain (e.g. "daily by product"), unit (e.g. "% or EUR"). ' +
  'Return ONLY a JSON object with keys: name, description, domain, type, grain, unit.';

const RECONCILE_SYSTEM_PROMPT =
  'You reconcile Business Factsheet prose with UseCase_Bracket.yaml for a governed analytics use case. ' +
  'The user edited one artifact; propose a patch for the OTHER artifact only. ' +
  'Return ONLY JSON: { "target": "factsheet" | "bracket", "summary": string, "patch": string (full updated content), "hints": string[] }. ' +
  'Never auto-merge silently — patch must be reviewable. Preserve YAML structure and markdown frontmatter.';

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

  const body = (await request.json()) as {
    mode?: string;
    prompt?: string;
    editedSource?: ReconcileEditedSource;
    prose?: string;
    bracket?: string;
    change_hint?: string;
  };

  if (body.mode === 'reconcile') {
    const editedSource = body.editedSource;
    const prose = body.prose ?? '';
    const bracketYaml = body.bracket ?? '';
    if (!editedSource || !prose || !bracketYaml) {
      return Response.json(
        { error: 'reconcile requires editedSource, prose, and bracket' },
        { status: 400 },
      );
    }

    const deterministic = reconcileDeterministic({
      editedSource,
      prose,
      bracketYaml,
      changeHint: body.change_hint,
    });

    const model = await createServerModel();
    if (model) {
      try {
        const { text } = await generateText({
          model,
          system: RECONCILE_SYSTEM_PROMPT,
          prompt: JSON.stringify({
            editedSource,
            change_hint: body.change_hint ?? 'user save',
            prose_length: prose.length,
            bracket_length: bracketYaml.length,
            prose_preview: prose.slice(0, 4000),
            bracket_preview: bracketYaml.slice(0, 4000),
            deterministic_hints: deterministic?.hints ?? [],
          }),
          maxOutputTokens: 4096,
        });
        const cleaned = text.trim().replace(/^```json\s*/i, '').replace(/\s*```$/i, '');
        const parsed = JSON.parse(cleaned) as {
          target?: string;
          summary?: string;
          patch?: string;
          hints?: string[];
        };
        if (parsed.target && parsed.patch) {
          return Response.json({
            target: parsed.target,
            summary: parsed.summary ?? 'AI proposed sync patch',
            patch: parsed.patch,
            hints: parsed.hints ?? [],
            engine: 'ai',
          });
        }
      } catch {
        // fall through to deterministic
      }
    }

    if (deterministic) {
      return Response.json({ ...deterministic, engine: 'deterministic' });
    }

    return Response.json({ target: null, summary: 'No sync patch needed', patch: null, hints: [] });
  }

  const { prompt = '' } = body;
  const model = await createServerModel();
  if (!model) {
    return Response.json(fallbackFromPrompt(prompt));
  }

  try {
    const { text } = await generateText({
      model,
      system: DRAFT_SYSTEM_PROMPT,
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
