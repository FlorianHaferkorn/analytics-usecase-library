/**
 * Assign/unassign a project to/from an org (ADR-0014, I-9.2). Requires org admin.
 *
 * POST body: { projectId: string } — assigns that project to this org.
 * DELETE ?projectId=... — unassigns; the project reverts to org_id = NULL
 * (solo mode, the primary/unchanged mode per ADR-0014, not a degraded fallback).
 */

import { requireAuth } from '@/lib/auth/session';
import { findOrCreateUser } from '@/lib/db/user-repo';
import { checkOrgAccess, setProjectOrg } from '@/lib/db/org-repo';
import { getProject } from '@/lib/db/project-repo';
import { logAuditEvent } from '@/lib/db/audit-repo';
import { apiSuccess, apiError, apiValidationError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

async function requireOrgAdmin(orgId: string) {
  const [user, authErr] = await requireAuth();
  if (authErr) return { user: null, error: authErr } as const;

  const actor = findOrCreateUser(user.email, user.name);
  if (!checkOrgAccess(orgId, actor.id, 'admin')) {
    return { user: null, error: apiError(ErrorCode.FORBIDDEN, 'Org admin role required', 403) } as const;
  }
  return { user, error: null } as const;
}

export async function POST(request: Request, { params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = await params;
  const { user, error } = await requireOrgAdmin(orgId);
  if (error) return error;

  const body = await request.json();
  const { projectId } = body as { projectId?: string };
  if (!projectId) return apiValidationError(['projectId required']);

  const project = getProject(projectId);
  if (!project) return apiError(ErrorCode.NOT_FOUND, 'Project not found', 404);
  // Refuse to steal a project already grouped under a different org — mirrors
  // the DELETE path's discipline. Only unassigned (org_id null) or
  // already-this-org (idempotent) projects may be assigned.
  if (project.org_id && project.org_id !== orgId) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Project already belongs to a different org — unassign it there first', 422);
  }

  setProjectOrg(projectId, orgId);
  logAuditEvent('project', projectId, 'update', {
    before: { org_id: project.org_id ?? null },
    after: { org_id: orgId },
  }, 'default', user!.email);

  return apiSuccess({ ok: true });
}

export async function DELETE(request: Request, { params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = await params;
  const { user, error } = await requireOrgAdmin(orgId);
  if (error) return error;

  const { searchParams } = new URL(request.url);
  const projectId = searchParams.get('projectId');
  if (!projectId) return apiValidationError(['projectId query param required']);

  const project = getProject(projectId);
  if (!project) return apiError(ErrorCode.NOT_FOUND, 'Project not found', 404);
  if (project.org_id !== orgId) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Project does not belong to this org', 422);
  }

  setProjectOrg(projectId, null);
  logAuditEvent('project', projectId, 'update', {
    before: { org_id: orgId },
    after: { org_id: null },
  }, 'default', user!.email);

  return apiSuccess({ ok: true });
}
