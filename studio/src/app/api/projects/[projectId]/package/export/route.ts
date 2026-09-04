import { ErrorCode } from '@/lib/api/error-codes';
import { requireRole } from '@/lib/auth/require-role';
import { exportProjectPackageHistory } from '@/lib/bridge/project-package-repository';
import { logAuditEvent } from '@/lib/db/audit-repo';
import { getProject } from '@/lib/db/project-repo';
import { apiError } from '@/lib/api/response';
import { packageRepositoryError } from '@/lib/project-package/http';

type RouteContext = { params: Promise<{ projectId: string }> };

export async function GET(_request: Request, { params }: RouteContext) {
  const { projectId } = await params;
  const [user, accessError] = await requireRole('viewer', projectId);
  if (accessError) return accessError;
  if (!getProject(projectId)) {
    return apiError(ErrorCode.NOT_FOUND, `Project '${projectId}' not found`, 404);
  }

  const result = await exportProjectPackageHistory(projectId);
  if (!result.ok || !result.value) return packageRepositoryError(result);
  logAuditEvent(
    'project',
    projectId,
    'export',
    {
      before: null,
      after: { package_revision_hash: result.value.head.revision_hash },
      justification: 'Exported complete immutable Project Package history',
    },
    projectId,
    user.email,
  );
  return new Response(Buffer.from(result.value.archive), {
    status: 200,
    headers: {
      'content-type': 'application/zip',
      'content-disposition': `attachment; filename="${projectId}-project-package-history.zip"`,
      'x-package-revision': result.value.head.revision_hash,
    },
  });
}
