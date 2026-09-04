import { ErrorCode } from '@/lib/api/error-codes';
import { apiError, apiSuccess } from '@/lib/api/response';
import {
  commitProjectPackageDraft,
  loadProjectPackage,
  type PackageSnapshot,
} from '@/lib/bridge/project-package-repository';
import { requireRole } from '@/lib/auth/require-role';
import { logAuditEvent } from '@/lib/db/audit-repo';
import { getProject } from '@/lib/db/project-repo';
import { MAX_PACKAGE_JSON_CHARS, contentLengthExceeds, packageRepositoryError } from '@/lib/project-package/http';
import type { PackageFile } from '@/lib/project-package/package-files';

type RouteContext = { params: Promise<{ projectId: string }> };
const REVISION_HASH = /^[a-f0-9]{64}$/;

function projectNotFound(projectId: string) {
  return apiError(ErrorCode.NOT_FOUND, `Project '${projectId}' not found`, 404);
}

export async function GET(request: Request, { params }: RouteContext) {
  const { projectId } = await params;
  const [, accessError] = await requireRole('viewer', projectId);
  if (accessError) return accessError;
  if (!getProject(projectId)) return projectNotFound(projectId);

  const revision = new URL(request.url).searchParams.get('revision') || undefined;
  if (revision && !REVISION_HASH.test(revision)) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'A valid revision hash is required', 422);
  }
  const result = await loadProjectPackage(projectId, revision);
  if (!result.ok || !result.value) return packageRepositoryError(result);
  return apiSuccess<PackageSnapshot>(result.value);
}

interface SaveRequest {
  expectedHeadRevisionHash: string | null;
  files: PackageFile[];
}

function isSaveRequest(value: unknown): value is SaveRequest {
  if (!value || typeof value !== 'object') return false;
  const body = value as Partial<SaveRequest>;
  return (
    (body.expectedHeadRevisionHash === null || typeof body.expectedHeadRevisionHash === 'string')
    && Array.isArray(body.files)
  );
}

export async function POST(request: Request, { params }: RouteContext) {
  const { projectId } = await params;
  const [user, accessError] = await requireRole('editor', projectId);
  if (accessError) return accessError;
  if (!getProject(projectId)) return projectNotFound(projectId);
  if (contentLengthExceeds(request, MAX_PACKAGE_JSON_CHARS)) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Project Package request is too large', 413);
  }

  let body: unknown;
  try {
    const raw = await request.text();
    if (raw.length > MAX_PACKAGE_JSON_CHARS) {
      return apiError(ErrorCode.VALIDATION_ERROR, 'Project Package request is too large', 413);
    }
    body = JSON.parse(raw);
  } catch {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid JSON body', 400);
  }
  if (!isSaveRequest(body)) {
    return apiError(
      ErrorCode.VALIDATION_ERROR,
      'Body must contain expectedHeadRevisionHash and a complete files array',
      422,
    );
  }

  const result = await commitProjectPackageDraft(projectId, body);
  if (!result.ok || !result.value) return packageRepositoryError(result);

  logAuditEvent(
    'project',
    projectId,
    'update',
    {
      before: { package_revision_hash: body.expectedHeadRevisionHash },
      after: { package_revision_hash: result.value.revision_hash },
      justification: 'Committed immutable Project Package revision',
    },
    projectId,
    user.email,
  );
  return apiSuccess({ revision: result.value }, 201);
}
