import { requireRole } from '@/lib/auth/require-role';
import { loadProjectPackage } from '@/lib/bridge/project-package-repository';
import { projectProjection } from '@/lib/project-package/projection';
import { packageRepositoryError } from '@/lib/project-package/http';
import { apiError, apiSuccess } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

export async function GET(request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  const [, denied] = await requireRole('viewer', projectId);
  if (denied) return denied;
  const revision = new URL(request.url).searchParams.get('revision') || undefined;
  if (revision && !/^[a-f0-9]{64}$/.test(revision)) return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid revision hash', 422);
  const result = await loadProjectPackage(projectId, revision);
  if (!result.ok || !result.value) return packageRepositoryError(result);
  try {
    const response = apiSuccess(projectProjection(projectId, result.value));
    response.headers.set('Cache-Control', 'private, no-store');
    return response;
  } catch (error) {
    return apiError(ErrorCode.CONFLICT, error instanceof Error ? error.message : 'Package projection unavailable', 409);
  }
}
