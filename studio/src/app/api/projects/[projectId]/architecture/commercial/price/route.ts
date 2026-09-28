import { requireRole } from '@/lib/auth/require-role';
import { projectPriceDelta } from '@/lib/bridge/project-price';
import { logAuditEvent } from '@/lib/db/audit-repo';

export const runtime = 'nodejs';
type Context = { params: Promise<{ projectId: string }> };
const json = (body: unknown, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'private, no-store' } });

/**
 * Private price delta of one alternative (WB-009). Admin only: the answer carries tenant money.
 * Never cached, never stored; the audit trail records that it was viewed, with hashes only.
 */
export async function GET(request: Request, context: Context) {
  const { projectId } = await context.params;
  const [user, denied] = await requireRole('admin', projectId);
  if (denied) return denied;
  const query = new URL(request.url).searchParams;
  const revision = query.get('revision'), decision = query.get('decision'), option = query.get('option');
  if (!revision || !/^[a-f0-9]{64}$/.test(revision)) return json({ error: 'Select a specific released project revision.' }, 422);
  if (!decision || !option || !/^[a-z][a-z0-9_]{0,63}$/.test(decision) || !/^[a-z][a-z0-9_]{0,63}$/.test(option)) {
    return json({ error: 'Select a recorded decision and one of its declared options.' }, 422);
  }
  const result = await projectPriceDelta(projectId, revision, decision, option);
  if (!result.ok || !result.value) return json({ error: result.error ?? 'Price delta unavailable.' }, result.status ?? 503);
  const value = result.value;
  if (value.project_ref !== projectId || value.baseline_revision_hash !== revision || value.decision_ref !== decision || value.alternative_option_ref !== option) {
    return json({ error: 'Price delta identity mismatch.' }, 409);
  }
  if (value.persist !== false) return json({ error: 'Price delta withheld: the result did not declare persist: false.' }, 409);
  if (value.status === 'evaluated') {
    logAuditEvent('export', `price_delta:${decision}:${option}`, 'export', {
      before: null,
      after: { kind: 'price_delta_viewed', revision_hash: revision, decision_ref: decision, option_ref: option,
        tenant_fingerprint_sha256: value.tenant_fingerprint_sha256 ?? null },
    }, projectId, user.email);
  }
  return json(value);
}
