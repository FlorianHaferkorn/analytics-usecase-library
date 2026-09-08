import { requireRole } from '@/lib/auth/require-role';
import { projectArchitecture, type ProjectArchitectureOutput } from '@/lib/bridge/project-architecture';
import { packageRepositoryError } from '@/lib/project-package/http';
import { apiError, apiSuccess } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

type Context = { params: Promise<{ projectId: string }> };
const HASH = /^[a-f0-9]{64}$/;

export async function GET(request: Request, { params }: Context) {
  const { projectId } = await params;
  const [, denied] = await requireRole('viewer', projectId);
  if (denied) return denied;
  const revision = new URL(request.url).searchParams.get('revision') || undefined;
  if (revision && !HASH.test(revision)) return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid revision hash', 422);
  const result = await projectArchitecture(projectId, revision);
  if (!result.ok || !result.value) return packageRepositoryError(result);
  const response = apiSuccess(result.value);
  response.headers.set('Cache-Control', 'private, no-store');
  return response;
}

export async function POST(request: Request, { params }: Context) {
  const { projectId } = await params;
  const [, denied] = await requireRole('editor', projectId);
  if (denied) return denied;
  let body;
  try {
    const raw = await request.text();
    if (raw.length > 5000) return apiError(ErrorCode.VALIDATION_ERROR, 'Request too large', 413);
    body = JSON.parse(raw);
    if (!body || !HASH.test(body.revisionHash) || body.confirmGeneration !== true || !['architecture_bundle', 'fabric_workspace_requests'].includes(body.target)) throw new Error('Invalid generation request');
  } catch { return apiError(ErrorCode.VALIDATION_ERROR, 'A pinned revision, supported target and explicit generation confirmation are required', 422); }
  const result = await projectArchitecture<ProjectArchitectureOutput>(projectId, body.revisionHash, body.target);
  if (!result.ok || !result.value) return packageRepositoryError(result);
  return new Response(JSON.stringify(result.value, null, 2), { headers: {
    'content-type': 'application/json', 'cache-control': 'private, no-store',
    'content-disposition': `attachment; filename="${projectId}-${body.target}-${body.revisionHash.slice(0, 12)}.json"`,
    'x-package-revision': body.revisionHash,
  } });
}
