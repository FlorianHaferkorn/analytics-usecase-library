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
