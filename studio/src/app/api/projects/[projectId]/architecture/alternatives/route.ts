import { apiErrorForStatus } from '@/lib/api/response';
import { requireRole } from '@/lib/auth/require-role';
import { projectAlternativeImpact } from '@/lib/bridge/project-alternatives';

export const runtime = 'nodejs';
type Context = { params: Promise<{ projectId: string }> };
const json = (body: unknown, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'private, no-store' } });
const fail = (message: string | undefined, status: number) => apiErrorForStatus(status, message, { 'Cache-Control': 'private, no-store' });

/** Read-only: compares a declared alternative with the released baseline. Never writes. */
export async function GET(request: Request, context: Context) {
  const { projectId } = await context.params;
  const [, denied] = await requireRole('viewer', projectId);
  if (denied) return denied;
  const query = new URL(request.url).searchParams;
  const revision = query.get('revision'), decision = query.get('decision'), option = query.get('option');
  if (!revision || !/^[a-f0-9]{64}$/.test(revision)) return fail('Select a specific released project revision.', 422);
  if (!decision || !option || !/^[a-z][a-z0-9_]{0,63}$/.test(decision) || !/^[a-z][a-z0-9_]{0,63}$/.test(option)) {
    return fail('Select a recorded decision and one of its declared options.', 422);
  }
  const result = await projectAlternativeImpact(projectId, revision, decision, option);
  if (!result.ok || !result.value) return fail(result.error ?? 'Alternative comparison unavailable.', result.status ?? 503);
  const value = result.value;
  if (value.project_ref !== projectId || value.baseline_revision_hash !== revision || value.decision_ref !== decision || value.alternative_option_ref !== option) {
    return fail('Alternative comparison identity mismatch.', 409);
  }
  if (value.baseline_unchanged !== true || value.approval_granted !== false || value.release_granted !== false || value.tenant_actions_performed !== false) {
    return fail('Comparison result violates the read-only contract.', 409);
  }
  return json(value);
}
