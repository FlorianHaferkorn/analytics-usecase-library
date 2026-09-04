import { ErrorCode } from '@/lib/api/error-codes';
import { apiError, apiSuccess } from '@/lib/api/response';
import { requireRole } from '@/lib/auth/require-role';
import { diffPackageRevisions } from '@/lib/bridge/project-package-repository';
import { getProject } from '@/lib/db/project-repo';
import { packageRepositoryError } from '@/lib/project-package/http';

type RouteContext = { params: Promise<{ projectId: string }> };
const REVISION_HASH = /^[a-f0-9]{64}$/;

export async function GET(request: Request, { params }: RouteContext) {
  const { projectId } = await params;
  const [, accessError] = await requireRole('viewer', projectId);
  if (accessError) return accessError;
  if (!getProject(projectId)) {
    return apiError(ErrorCode.NOT_FOUND, `Project '${projectId}' not found`, 404);
  }
  const query = new URL(request.url).searchParams;
  const fromRevision = query.get('from') || '';
  const toRevision = query.get('to') || '';
  if (!REVISION_HASH.test(fromRevision) || !REVISION_HASH.test(toRevision)) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Valid from and to revision hashes are required', 422);
  }

  const result = await diffPackageRevisions(projectId, fromRevision, toRevision);
  if (!result.ok || !result.value) return packageRepositoryError(result);
  return apiSuccess(result.value);
}
