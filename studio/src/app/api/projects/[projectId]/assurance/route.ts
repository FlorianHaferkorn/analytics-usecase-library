import { ErrorCode } from '@/lib/api/error-codes';
import { apiError, apiSuccess } from '@/lib/api/response';
import { requireRole } from '@/lib/auth/require-role';
import { assessProjectDelivery } from '@/lib/bridge/project-assurance';
import { packageRepositoryError } from '@/lib/project-package/http';

export async function GET(request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  const [, denied] = await requireRole('viewer', projectId);
  if (denied) return denied;
  const revision = new URL(request.url).searchParams.get('revision') || undefined;
  if (revision && !/^[a-f0-9]{64}$/.test(revision)) return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid revision hash', 422);
  const result = await assessProjectDelivery(projectId, revision);
  if (!result.ok || !result.value) return packageRepositoryError(result);
  const response = apiSuccess(result.value);
  response.headers.set('Cache-Control', 'private, no-store');
  return response;
}
