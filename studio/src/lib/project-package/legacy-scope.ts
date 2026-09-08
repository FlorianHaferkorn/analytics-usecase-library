import { requireRole } from '@/lib/auth/require-role';
import { apiError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

/** Old project/core aliases were global library reads/writes, not tenant isolation. */
export async function legacyProjectCore(request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  const read = request.method === 'GET';
  const [, denied] = await requireRole(read ? 'viewer' : 'editor', projectId);
  if (denied) return denied;
  return apiError(ErrorCode.UNSUPPORTED,
    read
      ? 'This legacy alias is a library resource, not project data. Use /api/core for library definitions or the project /view endpoint with a revision.'
      : 'Project changes must be committed through Project Package or saved as a project Discovery draft. Global library writes are not accepted here.',
    read ? 409 : 405);
}
