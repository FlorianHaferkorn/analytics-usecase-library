import { requireRole } from '@/lib/auth/require-role';
import { exportApprovedProjectInput } from '@/lib/bridge/project-package-repository';
import { apiError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';
import { getProject } from '@/lib/db/project-repo';
import { packageRepositoryError } from '@/lib/project-package/http';

type Context = { params: Promise<{ projectId: string }> };
const HASH = /^[a-f0-9]{64}$/;

async function handle(request: Request, context: Context, attest: boolean) {
  const { projectId } = await context.params;
  const [user, error] = await requireRole(attest ? 'admin' : 'viewer', projectId);
  if (error) return error;
  if (!getProject(projectId)) return apiError(ErrorCode.NOT_FOUND, 'Project not found', 404);
  let revision: unknown = new URL(request.url).searchParams.get('revision');
  let rationale: unknown;
  if (attest) {
    try {
      const raw = await request.text();
      if (raw.length > 5000) return apiError(ErrorCode.VALIDATION_ERROR, 'Request too large', 413);
      const body = JSON.parse(raw);
      revision = body.revisionHash;
      rationale = body.rationale;
      if (body.confirmInputBundleRelease !== true) throw new Error('Explicit confirmation required');
    } catch { return apiError(ErrorCode.VALIDATION_ERROR, 'Explicit input-bundle release confirmation and valid JSON are required', 422); }
  }
  if (typeof revision !== 'string' || !HASH.test(revision)) return apiError(ErrorCode.VALIDATION_ERROR, 'A pinned revision hash is required', 422);
  if (attest && (typeof rationale !== 'string' || rationale.trim().length < 20 || rationale.length > 2000)) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Provide a 20–2000 character release rationale', 422);
  }
  const result = await exportApprovedProjectInput(projectId, revision, attest ? { actor: user.email, rationale: rationale as string } : undefined);
  if (!result.ok || !result.value) return packageRepositoryError(result);
  return new Response(JSON.stringify(result.value, null, 2), { headers: {
    'content-type': 'application/json', 'cache-control': 'no-store',
    'content-disposition': `attachment; filename="${projectId}-approved-input-${revision.slice(0, 12)}.json"`,
    'x-package-revision': revision,
    'x-release-record': result.value.release.record_sha256,
  } });
}

export const GET = (request: Request, context: Context) => handle(request, context, false);
export const POST = (request: Request, context: Context) => handle(request, context, true);
