import { requireRole } from '@/lib/auth/require-role';
import { findRateField, projectCommercialImpact } from '@/lib/bridge/project-commercial';

export const runtime = 'nodejs';
type Context = { params: Promise<{ projectId: string }> };
const json = (body: unknown, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'private, no-store' } });

/** Read-only, rate-free commercial comparison. Editor role: canon hours are internal planning data. */
export async function GET(request: Request, context: Context) {
  const { projectId } = await context.params;
  const [, denied] = await requireRole('editor', projectId);
  if (denied) return denied;
  const query = new URL(request.url).searchParams;
  const revision = query.get('revision'), decision = query.get('decision'), option = query.get('option');
  if (!revision || !/^[a-f0-9]{64}$/.test(revision)) return json({ error: 'Select a specific released project revision.' }, 422);
  if (!decision || !option || !/^[a-z][a-z0-9_]{0,63}$/.test(decision) || !/^[a-z][a-z0-9_]{0,63}$/.test(option)) {
    return json({ error: 'Select a recorded decision and one of its declared options.' }, 422);
  }
  const result = await projectCommercialImpact(projectId, revision, decision, option);
  if (!result.ok || !result.value) return json({ error: result.error ?? 'Commercial comparison unavailable.' }, result.status ?? 503);
  const value = result.value;
  if (value.project_ref !== projectId || value.baseline_revision_hash !== revision || value.decision_ref !== decision || value.alternative_option_ref !== option) {
    return json({ error: 'Commercial comparison identity mismatch.' }, 409);
  }
  const leak = findRateField(value);
  if (leak || value.price_values_embedded !== false) return json({ error: 'Commercial comparison withheld: the result carried a rate or price field.' }, 409);
  return json(value);
}
