/**
 * Organization Repository — CRUD for organizations + org_members (ADR-0014, I-9.2).
 *
 * Mirrors project-repo.ts / rbac-repo.ts's split: this module owns organizations
 * themselves; membership lives alongside it since (unlike projects) an org has no
 * mutable state of its own beyond membership and its project list.
 */

import { getDb } from './sqlite';
import type { OrgMember, OrgRole } from '@/lib/auth/rbac-types';
import { orgRoleAtLeast } from '@/lib/auth/rbac-types';

export interface OrganizationRow {
  id: string;
  name: string;
  created_at: string;
}

export function listOrganizations(): OrganizationRow[] {
  const db = getDb();
  return db.prepare('SELECT * FROM organizations ORDER BY created_at DESC').all() as OrganizationRow[];
}

export function getOrganization(id: string): OrganizationRow | undefined {
  const db = getDb();
  return db.prepare('SELECT * FROM organizations WHERE id = ?').get(id) as OrganizationRow | undefined;
}

export function createOrganization(name: string): OrganizationRow {
  const db = getDb();
  const id = `org-${Date.now().toString(36)}`;
  db.prepare('INSERT INTO organizations (id, name) VALUES (?, ?)').run(id, name);
  return getOrganization(id)!;
}

/** projects.org_id = NULL is the primary, unchanged mode (ADR-0014) — deleting an org
 * reverts its projects to solo via ON DELETE SET NULL, not orphaned or blocked. */
export function deleteOrganization(id: string): boolean {
  const db = getDb();
  db.prepare('DELETE FROM org_members WHERE org_id = ?').run(id);
  const result = db.prepare('DELETE FROM organizations WHERE id = ?').run(id);
  return result.changes > 0;
}

/** Assign (or unassign, if orgId is null) a project to an org. */
export function setProjectOrg(projectId: string, orgId: string | null): void {
  const db = getDb();
  db.prepare('UPDATE projects SET org_id = ?, updated_at = datetime(\'now\') WHERE id = ?').run(orgId, projectId);
}

export function listOrgProjects(orgId: string): Array<{ id: string; name: string }> {
  const db = getDb();
  return db.prepare('SELECT id, name FROM projects WHERE org_id = ?').all(orgId) as Array<{ id: string; name: string }>;
}

// Named binds below (@orgId/@userId), not positional — a positional param-order
// bug in getOrgMember/removeOrgMember silently broke the whole org-fallback RBAC
// path during self-testing (SQL text said org_id first, calls passed userId
// first). Named binds make that whole mistake class impossible to reintroduce.

export function addOrgMember(
  orgId: string,
  userId: string,
  orgRole: OrgRole,
  businessRoleId: string | null = null,
): OrgMember {
  const db = getDb();
  db.prepare(
    'INSERT OR REPLACE INTO org_members (user_id, org_id, org_role, business_role_id) VALUES (@userId, @orgId, @orgRole, @businessRoleId)',
  ).run({ userId, orgId, orgRole, businessRoleId });
  return getOrgMember(orgId, userId)!;
}

/**
 * Set (or clear, with null) a member's business_role_id — a display-only
 * link to core/organization/org_roles.yaml (ADR-0014 O-3). Never touches
 * org_role or any RBAC resolution path.
 */
export function setMemberBusinessRole(orgId: string, userId: string, businessRoleId: string | null): OrgMember | undefined {
  const db = getDb();
  db.prepare(
    'UPDATE org_members SET business_role_id = @businessRoleId WHERE org_id = @orgId AND user_id = @userId',
  ).run({ orgId, userId, businessRoleId });
  return getOrgMember(orgId, userId);
}

export function removeOrgMember(orgId: string, userId: string): boolean {
  const db = getDb();
  const result = db.prepare('DELETE FROM org_members WHERE org_id = @orgId AND user_id = @userId').run({ orgId, userId });
  return result.changes > 0;
}

export function getOrgMember(orgId: string, userId: string): OrgMember | undefined {
  const db = getDb();
  return db.prepare('SELECT * FROM org_members WHERE org_id = @orgId AND user_id = @userId').get({ orgId, userId }) as OrgMember | undefined;
}

export function listOrgMembers(orgId: string): OrgMember[] {
  const db = getDb();
  return db.prepare('SELECT * FROM org_members WHERE org_id = ? ORDER BY created_at').all(orgId) as OrgMember[];
}

export interface OrgMemberWithUser extends OrgMember {
  email: string;
  name: string;
}

/** listOrgMembers, joined with users for display (email/name) — for the management UI. */
export function listOrgMembersWithDetails(orgId: string): OrgMemberWithUser[] {
  const db = getDb();
  return db.prepare(
    `SELECT om.*, u.email, u.name
     FROM org_members om
     JOIN users u ON u.id = om.user_id
     WHERE om.org_id = ?
     ORDER BY om.created_at`,
  ).all(orgId) as OrgMemberWithUser[];
}

/** All org memberships for a user, across every org (JWT-token shape, ADR-0014 Festlegung 5). */
export function listUserOrgMemberships(userId: string): OrgMember[] {
  const db = getDb();
  return db.prepare('SELECT * FROM org_members WHERE user_id = ?').all(userId) as OrgMember[];
}

export function checkOrgAccess(orgId: string, userId: string, minRole: OrgRole): OrgMember | undefined {
  const member = getOrgMember(orgId, userId);
  if (!member) return undefined;
  return orgRoleAtLeast(member.org_role, minRole) ? member : undefined;
}
