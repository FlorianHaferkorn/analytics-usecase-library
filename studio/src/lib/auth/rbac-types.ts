/**
 * RBAC Type Definitions — project-level role-based access control.
 */

export type ProjectRole = 'admin' | 'editor' | 'viewer';

export interface UserRecord {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface ProjectMember {
  user_id: string;
  project_id: string;
  role: ProjectRole;
  created_at: string;
}

/** Role hierarchy: higher index = more permissions. */
export const ROLE_HIERARCHY: readonly ProjectRole[] = ['viewer', 'editor', 'admin'] as const;

export function roleAtLeast(userRole: ProjectRole, minRole: ProjectRole): boolean {
  return ROLE_HIERARCHY.indexOf(userRole) >= ROLE_HIERARCHY.indexOf(minRole);
}

/**
 * Org-level roles (ADR-0014). Deliberately a separate vocabulary from ProjectRole —
 * an org role is not a project access level, it only ever becomes one via the
 * conservative fallback mapping in resolveProjectAccess (checkAccess).
 */
export type OrgRole = 'owner' | 'admin' | 'member';

export interface OrgMember {
  user_id: string;
  org_id: string;
  org_role: OrgRole;
  created_at: string;
}

const ORG_ROLE_HIERARCHY: readonly OrgRole[] = ['member', 'admin', 'owner'] as const;

export function orgRoleAtLeast(role: OrgRole, minRole: OrgRole): boolean {
  return ORG_ROLE_HIERARCHY.indexOf(role) >= ORG_ROLE_HIERARCHY.indexOf(minRole);
}

/**
 * Fallback project-access level derived from an org role, when no explicit
 * project_members row exists (ADR-0014 Festlegung 4b). Bewusst konservativ:
 * owner/admin -> admin, member -> viewer, no path to 'editor' from org
 * membership alone.
 */
export function projectRoleFromOrgRole(orgRole: OrgRole): ProjectRole {
  return orgRole === 'owner' || orgRole === 'admin' ? 'admin' : 'viewer';
}
