/**
 * Organization detail API — get (org + members + projects) and delete
 * (ADR-0014, I-9.2).
 */

import { requireAuth } from '@/lib/auth/session';
import { findOrCreateUser } from '@/lib/db/user-repo';
import { getOrganization, deleteOrganization, listOrgMembersWithDetails, listOrgProjects, checkOrgAccess } from '@/lib/db/org-repo';
import { logAuditEvent } from '@/lib/db/audit-repo';
import { apiSuccess, apiError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

export async function GET(_request: Request, { params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = await params;
  const [user, authErr] = await requireAuth();
  if (authErr) return authErr;

  const organization = getOrganization(orgId);
  if (!organization) return apiError(ErrorCode.NOT_FOUND, 'Organization not found', 404);

  const dbUser = findOrCreateUser(user.email, user.name);
  if (!checkOrgAccess(orgId, dbUser.id, 'member')) {
    return apiError(ErrorCode.FORBIDDEN, 'Org membership required', 403);
  }

  return apiSuccess({
    organization,
    members: listOrgMembersWithDetails(orgId),
    projects: listOrgProjects(orgId),
  });
}

export async function DELETE(_request: Request, { params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = await params;
  const [user, authErr] = await requireAuth();
  if (authErr) return authErr;

  const organization = getOrganization(orgId);
  if (!organization) return apiError(ErrorCode.NOT_FOUND, 'Organization not found', 404);

  const dbUser = findOrCreateUser(user.email, user.name);
  if (!checkOrgAccess(orgId, dbUser.id, 'owner')) {
    return apiError(ErrorCode.FORBIDDEN, 'Org owner role required', 403);
  }

  deleteOrganization(orgId);
  // Projects fall back to org_id = NULL (solo mode) via ON DELETE SET NULL — not orphaned.
  logAuditEvent('org', orgId, 'delete', {
    before: { name: organization.name },
    after: null,
  }, 'default', user.email);

  return apiSuccess({ deleted: true });
}
