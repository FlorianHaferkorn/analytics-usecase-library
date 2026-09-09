import { requireRole } from '@/lib/auth/require-role';
import { projectDecisions, type DecisionApplication, type DecisionPreview } from '@/lib/bridge/project-decisions';

export const runtime = 'nodejs';
type Context = { params: Promise<{ projectId: string }> };
const hash = (value: unknown): value is string => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const json = (body: unknown, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'private, no-store' } });

export async function GET(request: Request, context: Context) {
  const { projectId } = await context.params;
  const [, denied] = await requireRole('viewer', projectId);
  if (denied) return denied;
  const revision = new URL(request.url).searchParams.get('revision');
  if (!hash(revision)) return json({ error: 'Select a specific project revision.' }, 422);
  const result = await projectDecisions<DecisionPreview>(projectId, revision);
  if (!result.ok || !result.value) return json({ error: result.error ?? 'Decision review unavailable.' }, result.status ?? 503);
  if (result.value.project_ref !== projectId || result.value.revision_hash !== revision) return json({ error: 'Decision review identity mismatch.' }, 409);
  return json(result.value);
}

export async function POST(request: Request, context: Context) {
  const { projectId } = await context.params;
  const [user, denied] = await requireRole('editor', projectId);
  if (denied) return denied;
  let body: Record<string, unknown>;
  try {
    const raw = await request.text();
    if (raw.length > 12_000) return json({ error: 'Review request is too large.' }, 413);
    body = JSON.parse(raw);
  } catch { return json({ error: 'Invalid review request.' }, 400); }
  if (!body || Array.isArray(body) || Object.keys(body).some(key => !['revisionHash', 'previewHash', 'rationale', 'confirmed'].includes(key))
    || !hash(body.revisionHash) || !hash(body.previewHash) || body.confirmed !== true
    || typeof body.rationale !== 'string' || body.rationale.trim().length < 20 || body.rationale.length > 4000) {
    return json({ error: 'A pinned preview, review rationale and explicit confirmation are required. Values and decisions are read from the Package.' }, 422);
  }
  const result = await projectDecisions<DecisionApplication>(projectId, body.revisionHash, {
    previewHash: body.previewHash, rationale: body.rationale.trim(), actor: user.email,
  });
  if (!result.ok || !result.value) return json({ error: result.error ?? 'Architecture update failed.' }, result.status ?? 503);
  if (result.value.project_ref !== projectId || result.value.parent_revision_hash !== body.revisionHash || !hash(result.value.revision_hash)) {
    return json({ error: 'Architecture update identity mismatch. Reload the Package before continuing.' }, 409);
  }
  return json(result.value);
}
