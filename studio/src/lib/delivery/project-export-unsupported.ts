import { requireRole } from '@/lib/auth/require-role';
import { apiError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

export async function unsupportedProjectExport(_request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  const [, error] = await requireRole('viewer', projectId);
  if (error) return error;
  return apiError(ErrorCode.UNSUPPORTED, 'This target does not yet compile from pinned project inputs. Use Project Package to release approved inputs, or switch to Library for exploratory previews.', 409);
}
