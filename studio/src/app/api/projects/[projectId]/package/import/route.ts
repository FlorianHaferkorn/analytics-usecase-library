import { ErrorCode } from '@/lib/api/error-codes';
import { apiError, apiSuccess } from '@/lib/api/response';
import { requireRole } from '@/lib/auth/require-role';
import { importProjectPackageHistory } from '@/lib/bridge/project-package-repository';
import { logAuditEvent } from '@/lib/db/audit-repo';
import { getProject } from '@/lib/db/project-repo';
import {
  MAX_PACKAGE_ARCHIVE_BYTES,
  contentLengthExceeds,
  packageRepositoryError,
} from '@/lib/project-package/http';

type RouteContext = { params: Promise<{ projectId: string }> };

export async function POST(request: Request, { params }: RouteContext) {
  const { projectId } = await params;
  const [user, accessError] = await requireRole('admin', projectId);
  if (accessError) return accessError;
  if (!getProject(projectId)) {
    return apiError(ErrorCode.NOT_FOUND, `Project '${projectId}' not found`, 404);
  }
  if (contentLengthExceeds(request, MAX_PACKAGE_ARCHIVE_BYTES)) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Project Package archive is too large', 413);
  }

  const archive = new Uint8Array(await request.arrayBuffer());
  if (archive.byteLength === 0 || archive.byteLength > MAX_PACKAGE_ARCHIVE_BYTES) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Project Package archive size is outside the allowed range', 413);
  }
  const result = await importProjectPackageHistory(projectId, archive);
  if (!result.ok || !result.value) return packageRepositoryError(result);

  logAuditEvent(
    'project',
    projectId,
    'update',
    {
      before: { package_revision_hash: null },
      after: { package_revision_hash: result.value.revision_hash },
      justification: 'Imported and verified complete Project Package history',
    },
    projectId,
    user.email,
  );
  return apiSuccess({ head: result.value }, 201);
}
