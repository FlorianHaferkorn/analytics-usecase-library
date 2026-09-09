import { requireRunnerAccess, runnerAccessReadiness, runnerAccessReadinessFailure } from '@/lib/auth/runner-access';
import { projectRunner, type RunnerApproval, type RunnerEvidence, type RunnerResult, type RunnerStatus } from '@/lib/bridge/project-runner';

export const runtime = 'nodejs';
type Context = { params: Promise<{ projectId: string }> };
const hash = (value: unknown): value is string => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const json = (body: unknown, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'private, no-store' } });

export async function GET(request: Request, context: Context) {
  const { projectId } = await context.params;
  const [access, denied] = await requireRunnerAccess(projectId);
  if (denied) return runnerAccessReadinessFailure(denied);
  const params = new URL(request.url).searchParams;
  const revision = params.get('revision'), approval = params.get('approval');
  if (!hash(revision) || (approval !== null && !hash(approval))) return json({ error: 'A pinned version and valid approval ID are required.' }, 422);
  if (approval) {
    const result = await projectRunner<RunnerEvidence>(projectId, revision, access.actor, { mode: 'outcome', approvalId: approval });
    if (!result.ok || !result.value) return json({ error: result.error }, result.status ?? 503);
    const receipt = result.value.receipt;
    if (receipt?.project_ref !== projectId || receipt.revision_hash !== revision || receipt.approval_id !== approval) return json({ error: 'Saved approval identity mismatch.' }, 409);
    return json(result.value);
  }
  const accessChecks = runnerAccessReadiness(access);
  const result = await projectRunner<RunnerStatus>(projectId, revision, access.actor, { mode: 'status' });
  if (!result.ok || !result.value) return json({
    error: result.error,
    checks: [...accessChecks, {
      id: 'runner_host', title: 'Protected runner host', state: 'missing',
      detail: 'The protected host readiness check could not complete. No tenant readiness or execution capability has been established.',
      action: 'Ask the host administrator to validate the private runner configuration and the configured Python runtime, then refresh readiness. Do not paste configuration secrets into Studio.',
    }],
    checked_at: new Date().toISOString(),
  }, result.status ?? 503);
  if (result.value.project_ref !== projectId) return json({ error: 'Runner project identity mismatch.' }, 409);
  const mutationsReady = accessChecks.every(check => check.state === 'configured');
  return json({
    ...result.value,
    can_approve: result.value.can_approve === true && mutationsReady,
    can_execute: result.value.can_execute === true && mutationsReady,
    checks: [...accessChecks, ...(result.value.checks ?? [])], checked_at: new Date().toISOString(),
  });
}

export async function POST(request: Request, context: Context) {
  const { projectId } = await context.params;
  const [access, denied] = await requireRunnerAccess(projectId, request, true);
  if (denied) return denied;
  let body: Record<string, unknown>;
  try {
    const raw = await request.text();
    if (raw.length > 2_000_000) return json({ error: 'Runner request is too large.' }, 413);
    body = JSON.parse(raw);
  } catch { return json({ error: 'Invalid runner request.' }, 400); }
  if (!body || typeof body !== 'object' || Array.isArray(body) || !hash(body.revisionHash) || body.confirmed !== true) return json({ error: 'Exact version and explicit confirmation required.' }, 422);
  if (body.mode === 'approve') {
    if (Object.keys(body).some(key => !['mode', 'revisionHash', 'confirmed', 'plan', 'rationale'].includes(key))
      || !body.plan || typeof body.plan !== 'object' || Array.isArray(body.plan)
      || typeof body.rationale !== 'string' || body.rationale.trim().length < 20 || body.rationale.length > 2000) return json({ error: 'Review the exact workspace plan and supply a 20–2000 character rationale.' }, 422);
    const plan = body.plan as Record<string, unknown>;
    if (plan.project_ref !== projectId || plan.revision_hash !== body.revisionHash || !hash(plan.plan_sha256)) return json({ error: 'Plan does not belong to this project version.' }, 422);
    const result = await projectRunner<RunnerApproval>(projectId, body.revisionHash, access.actor, { mode: 'approve', plan, rationale: body.rationale.trim() });
    if (!result.ok || !result.value) return json({ error: result.error }, result.status ?? 503);
    if (result.value.project_ref !== projectId || result.value.revision_hash !== body.revisionHash || result.value.plan_sha256 !== plan.plan_sha256) return json({ error: 'Approval outcome could not be verified. Inspect saved records before retrying.' }, 409);
    return json(result.value);
  }
  if (body.mode === 'execute') {
    if (Object.keys(body).some(key => !['mode', 'revisionHash', 'confirmed', 'approvalId'].includes(key)) || !hash(body.approvalId)) return json({ error: 'Execution accepts only a saved approval ID and the pinned version.' }, 422);
    const result = await projectRunner<RunnerResult>(projectId, body.revisionHash, access.actor, { mode: 'execute', approvalId: body.approvalId });
    if (!result.ok || !result.value) return json({ error: result.error }, result.status ?? 503);
    if (result.value.project_ref !== projectId || result.value.revision_hash !== body.revisionHash || result.value.approval_id !== body.approvalId) return json({ error: 'Execution outcome is uncertain. Retrieve the saved evidence; do not retry execution.' }, 409);
    return json(result.value);
  }
  return json({ error: 'Unsupported runner action.' }, 422);
}
