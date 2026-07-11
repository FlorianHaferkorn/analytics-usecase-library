/**
 * Org-owner break-glass override (ADR-0014 O-4).
 *
 * Festlegung 4's "no merge" rule means an explicit project_members row always
 * wins over an org-derived fallback role — which can leave an org owner
 * capped below their org role on a project of their own org (an old, narrow
 * project_members row from before the project joined the org, or before they
 * became owner). Rather than silently merging roles inside checkAccess's
 * resolution (which Festlegung 4 explicitly rejects), this is a separate,
 * explicit, audited action: the org owner deliberately grants THEMSELVES an
 * admin project_members row on a project of their own org, with a required
 * justification. checkAccess's two-stage resolution is untouched — after
 * this call it just resolves the (now real) explicit row, same as any other
 * project_members grant.
 *
 * Deliberately self-only (not "any org owner can grant anyone admin on any
 * of the org's projects" — that would reopen the self-escalation surface
 * members/route.ts already closes for org-role grants).
 *
 * POST only fires if the actor is NOT already admin (via an explicit row OR
 * the org fallback) — otherwise this would double as a general-purpose
 * "grab admin on any of my org's projects" shortcut (e.g. assign a solo
 * project into the org, then break-glass, even though the org fallback
 * already gives an owner admin there for free). Restricting it to the actual
 * lockout case keeps this an honest recovery tool, not a convenience path.
 *
 * DELETE lets the actor step back down from their OWN explicit row, so the
 * override isn't a permanent one-way grant — reverting to normal two-stage
 * resolution (which then correctly reflects e.g. a later org-role demotion,
 * something a stale explicit row would otherwise mask).
 */

import { requireAuth, type SessionUser } from '@/lib/auth/session';
import { findOrCreateUser } from '@/lib/db/user-repo';
import { checkOrgAccess } from '@/lib/db/org-repo';
import { getProject } from '@/lib/db/project-repo';
import { addProjectMember, checkAccess, getProjectMember, removeProjectMember } from '@/lib/db/rbac-repo';
import { logAuditEvent } from '@/lib/db/audit-repo';
import { apiSuccess, apiError, apiValidationError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';
import type { UserRecord } from '@/lib/auth/rbac-types';

async function requireOrgOwnerOnOrgProject(
  orgId: string,
  projectId: string | undefined,
): Promise<
  | { user: SessionUser; actor: UserRecord; error: null }
  | { user: null; actor: null; error: Response }
> {
  const [user, authErr] = await requireAuth();
  if (authErr) return { user: null, actor: null, error: authErr };

  const actor = findOrCreateUser(user.email, user.name);
  if (!checkOrgAccess(orgId, actor.id, 'owner')) {
    return { user: null, actor: null, error: apiError(ErrorCode.FORBIDDEN, 'Org owner role required for break-glass override', 403) };
  }

  if (!projectId) return { user: null, actor: null, error: apiValidationError(['projectId required']) };

  const project = getProject(projectId);
  if (!project) return { user: null, actor: null, error: apiError(ErrorCode.NOT_FOUND, 'Project not found', 404) };
  if (project.org_id !== orgId) {
    return { user: null, actor: null, error: apiError(ErrorCode.VALIDATION_ERROR, 'Project does not belong to this org', 422) };
  }

  return { user, actor, error: null };
}

export async function POST(request: Request, { params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = await params;
  const body = await request.json();
  const { projectId, justification } = body as { projectId?: string; justification?: string };

  const { user, actor, error } = await requireOrgOwnerOnOrgProject(orgId, projectId);
  if (error) return error;
  if (!justification?.trim()) return apiValidationError(['justification is required for a break-glass override']);

  if (checkAccess(projectId!, actor.id, 'admin')) {
    return apiError(
      ErrorCode.VALIDATION_ERROR,
      'You already have admin access to this project — break-glass is only for recovering from a role capped below your org role',
      422,
    );
  }

  const before = getProjectMember(projectId!, actor.id);
  addProjectMember(projectId!, actor.id, 'admin');

  logAuditEvent('project_member', `${projectId}::${actor.id}`, 'break_glass_override', {
    before: before ? { role: before.role } : null,
    after: { role: 'admin' },
    justification: justification.trim(),
  }, projectId!, user.email);

  return apiSuccess({ granted: true, projectId, role: 'admin' as const });
}

export async function DELETE(request: Request, { params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = await params;
  const { searchParams } = new URL(request.url);
  const projectId = searchParams.get('projectId') ?? undefined;

  const { user, actor, error } = await requireOrgOwnerOnOrgProject(orgId, projectId);
  if (error) return error;

  const before = getProjectMember(projectId!, actor.id);
  if (!before) {
    return apiError(ErrorCode.NOT_FOUND, 'No explicit project role to revert for this actor', 404);
  }

  removeProjectMember(projectId!, actor.id);

  logAuditEvent('project_member', `${projectId}::${actor.id}`, 'break_glass_revert', {
    before: { role: before.role },
    after: null,
  }, projectId!, user.email);

  return apiSuccess({ reverted: true, projectId });
}
