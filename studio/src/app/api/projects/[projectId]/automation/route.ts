import { requireRole } from '@/lib/auth/require-role';
import { projectAutomation, type AutomationOutput } from '@/lib/bridge/project-automation';
import { packageRepositoryError } from '@/lib/project-package/http';
import { apiError, apiSuccess } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';
import type { AutomationTarget } from '@/lib/bridge/project-automation';

type Context = {params: Promise<{projectId: string}>};
const HASH = /^[a-f0-9]{64}$/;
const TARGETS = new Set(['architecture_bundle', 'fabric_workspace_requests', 'fabric_item_requests', 'proposal_assumptions']);

export async function GET(request: Request, {params}: Context) {
  const {projectId} = await params;
  const [, denied] = await requireRole('viewer', projectId);
  if (denied) return denied;
  const revision = new URL(request.url).searchParams.get('revision');
  const runId = new URL(request.url).searchParams.get('run');
  if (!revision || !HASH.test(revision)) return apiError(ErrorCode.VALIDATION_ERROR, 'A pinned project revision is required', 422);
  if (runId && !HASH.test(runId)) return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid run fingerprint', 422);
  const result = runId ? await projectAutomation<AutomationOutput>(projectId, revision, undefined, runId) : await projectAutomation(projectId, revision);
  if (!result.ok || !result.value) return packageRepositoryError(result);
  // Canon hours and bands are internal planning data: same role as /architecture/commercial.
  const runTargets = (result.value as {report?: {targets?: unknown}}).report?.targets;
  if (runId && Array.isArray(runTargets) && runTargets.includes('proposal_assumptions')) {
    const [, restricted] = await requireRole('editor', projectId);
    if (restricted) return restricted;
  }
  const response = apiSuccess(result.value);
  response.headers.set('Cache-Control', 'private, no-store');
  return response;
}

export async function POST(request: Request, {params}: Context) {
  const {projectId} = await params;
  const [user, denied] = await requireRole('editor', projectId);
  if (denied) return denied;
  let body: {revisionHash: string; targets: AutomationTarget[]};
  try {
    const raw = await request.text();
    if (raw.length > 5000) return apiError(ErrorCode.VALIDATION_ERROR, 'Request too large', 413);
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed.revisionHash !== 'string' || !HASH.test(parsed.revisionHash) || parsed.confirmGeneration !== true ||
      !Array.isArray(parsed.targets) || !parsed.targets.length || parsed.targets.length > TARGETS.size ||
      new Set(parsed.targets).size !== parsed.targets.length || parsed.targets.some((target: unknown) => typeof target !== 'string' || !TARGETS.has(target)) ||
      Object.keys(parsed).some(key => !['revisionHash', 'targets', 'confirmGeneration'].includes(key))) throw new Error('Invalid request');
    body = parsed;
  } catch { return apiError(ErrorCode.VALIDATION_ERROR, 'Select supported outputs and explicitly confirm generation for the pinned revision', 422); }
  const result = await projectAutomation<AutomationOutput>(projectId, body.revisionHash, {actor: user.email, targets: body.targets});
  if (!result.ok || !result.value) return packageRepositoryError(result);
  return new Response(JSON.stringify(result.value, null, 2), {headers: {
    'content-type': 'application/json', 'cache-control': 'private, no-store',
    'content-disposition': `attachment; filename="${projectId}-generation-${body.revisionHash.slice(0, 12)}.json"`,
    'x-package-revision': body.revisionHash,
  }});
}
