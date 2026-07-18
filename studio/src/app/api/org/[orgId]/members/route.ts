/**
 * Organization membership API — add/remove a member (ADR-0014, I-9.2).
 *
 * Requires org admin (owner or admin) to mutate, EXCEPT granting the 'owner'
 * role itself, which requires the actor to already be an owner — an admin
 * cannot self-escalate or hand out ownership. Removing the org's last owner
 * is refused outright (would orphan the org: only an owner can delete it or
 * grant further ownership). No self-approval-lock equivalent otherwise
 * (unlike bracket approval) — org membership grants aren't a reviewable
 * proposal against a submission, they're a direct admin action, same as
 * project_members today (addProjectMember has no such lock either).
 *
 * Does NOT auto-provision a user for an email that has never logged in —
 * that would silently answer ADR-0014's O-1 (invitation/onboarding UX) with
 * an eager-create policy instead of leaving it genuinely open. A member can
 * only be added once they exist in `users` (i.e. have signed in at least
 * once).
 */

import { requireAuth } from '@/lib/auth/session';
import { findOrCreateUser, findUserByEmail } from '@/lib/db/user-repo';
import { addOrgMember, removeOrgMember, setMemberBusinessRole, checkOrgAccess, listOrgMembers, getOrgMember } from '@/lib/db/org-repo';
import { loadOrgRoles } from '@/lib/core/org-role-loader';
import { logAuditEvent } from '@/lib/db/audit-repo';
import type { OrgRole } from '@/lib/auth/rbac-types';
import { apiSuccess, apiError, apiValidationError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

const VALID_ORG_ROLES: OrgRole[] = ['owner', 'admin', 'member'];

/** businessRoleId must resolve against core/organization/org_roles.yaml, or be omitted/null. */
async function validateBusinessRoleId(businessRoleId: unknown): Promise<string | null | undefined> {
  if (businessRoleId === undefined || businessRoleId === null || businessRoleId === '') return null;
  if (typeof businessRoleId !== 'string') return undefined;
  const roles = await loadOrgRoles();
  return roles.has(businessRoleId) ? businessRoleId : undefined;
}

export async function POST(request: Request, { params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = await params;
  const [user, authErr] = await requireAuth();
  if (authErr) return authErr;

  const actor = findOrCreateUser(user.email, user.name);
  if (!checkOrgAccess(orgId, actor.id, 'admin')) {
    return apiError(ErrorCode.FORBIDDEN, 'Org admin role required', 403);
  }

  const body = await request.json();
  const { email, orgRole, businessRoleId: rawBusinessRoleId } = body as { email?: string; orgRole?: string; businessRoleId?: string };
  if (!email?.trim() || !orgRole || !VALID_ORG_ROLES.includes(orgRole as OrgRole)) {
    return apiValidationError(['email required, orgRole must be one of owner/admin/member']);
  }

  const businessRoleId = await validateBusinessRoleId(rawBusinessRoleId);
  if (businessRoleId === undefined) {
    return apiValidationError(['businessRoleId does not match any role in core/organization/org_roles.yaml']);
  }

  // Granting 'owner' requires the actor to already be an owner — an admin
  // cannot hand out or self-escalate to ownership.
  if (orgRole === 'owner' && !checkOrgAccess(orgId, actor.id, 'owner')) {
    return apiError(ErrorCode.FORBIDDEN, 'Only an existing owner can grant the owner role', 403);
  }

  const targetUser = findUserByEmail(email.trim());
  if (!targetUser) {
    return apiError(ErrorCode.NOT_FOUND, 'No user found for that email — they must sign in at least once first', 404);
  }

  const member = addOrgMember(orgId, targetUser.id, orgRole as OrgRole, businessRoleId);

  logAuditEvent('org_member', `${orgId}::${targetUser.id}`, 'add_member', {
    before: null,
    after: { email: email.trim(), orgRole, businessRoleId },
  }, 'default', user.email);

  return apiSuccess({ member });
}

/** Update an existing member's business_role_id (ADR-0014 O-3) — display-only, never org_role. */
export async function PATCH(request: Request, { params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = await params;
  const [user, authErr] = await requireAuth();
  if (authErr) return authErr;

  const actor = findOrCreateUser(user.email, user.name);
  if (!checkOrgAccess(orgId, actor.id, 'admin')) {
    return apiError(ErrorCode.FORBIDDEN, 'Org admin role required', 403);
  }

  const body = await request.json();
  const { email, businessRoleId: rawBusinessRoleId } = body as { email?: string; businessRoleId?: string | null };
  if (!email?.trim()) {
    return apiValidationError(['email required']);
  }

  const businessRoleId = await validateBusinessRoleId(rawBusinessRoleId);
  if (businessRoleId === undefined) {
    return apiValidationError(['businessRoleId does not match any role in core/organization/org_roles.yaml']);
  }

  const targetUser = findUserByEmail(email.trim());
  if (!targetUser) return apiError(ErrorCode.NOT_FOUND, 'User not found', 404);

  const before = getOrgMember(orgId, targetUser.id);
  if (!before) return apiError(ErrorCode.NOT_FOUND, 'User is not a member of this organization', 404);

  const member = setMemberBusinessRole(orgId, targetUser.id, businessRoleId);

  logAuditEvent('org_member', `${orgId}::${targetUser.id}`, 'update_business_role', {
    before: { businessRoleId: before.business_role_id },
    after: { businessRoleId },
  }, 'default', user.email);

  return apiSuccess({ member });
}

export async function DELETE(request: Request, { params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = await params;
  const [user, authErr] = await requireAuth();
  if (authErr) return authErr;

  const actor = findOrCreateUser(user.email, user.name);
  if (!checkOrgAccess(orgId, actor.id, 'admin')) {
    return apiError(ErrorCode.FORBIDDEN, 'Org admin role required', 403);
  }

  const { searchParams } = new URL(request.url);
  const email = searchParams.get('email');
  if (!email) return apiValidationError(['email query param required']);

  const targetUser = findUserByEmail(email);
  if (!targetUser) return apiError(ErrorCode.NOT_FOUND, 'User not found', 404);

  const members = listOrgMembers(orgId);
  const target = members.find((m) => m.user_id === targetUser.id);
  if (target?.org_role === 'owner') {
    const ownerCount = members.filter((m) => m.org_role === 'owner').length;
    if (ownerCount <= 1) {
      return apiError(ErrorCode.VALIDATION_ERROR, 'Cannot remove the org\'s last owner — grant ownership to someone else first', 422);
    }
  }

  removeOrgMember(orgId, targetUser.id);

  logAuditEvent('org_member', `${orgId}::${targetUser.id}`, 'remove_member', {
    before: { email },
    after: null,
  }, 'default', user.email);

  return apiSuccess({ removed: true });
}
