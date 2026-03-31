/**
 * RBAC Repository — project membership and access control.
 *
 * Each project has members with roles: admin, editor, viewer.
 * The user who creates a project is auto-assigned as admin.
 */

import { getDb } from './sqlite';
import type { ProjectMember, ProjectRole } from '@/lib/auth/rbac-types';
import { roleAtLeast } from '@/lib/auth/rbac-types';

/** Add a member to a project with a specific role. */
export function addProjectMember(
  projectId: string,
  userId: string,
  role: ProjectRole,
): ProjectMember {
  const db = getDb();
  db.prepare(
    'INSERT OR REPLACE INTO project_members (user_id, project_id, role) VALUES (?, ?, ?)',
  ).run(userId, projectId, role);

  return db.prepare(
    'SELECT * FROM project_members WHERE user_id = ? AND project_id = ?',
  ).get(userId, projectId) as ProjectMember;
}

/** Remove a member from a project. */
export function removeProjectMember(projectId: string, userId: string): boolean {
  const db = getDb();
  const result = db.prepare(
    'DELETE FROM project_members WHERE user_id = ? AND project_id = ?',
  ).run(userId, projectId);
  return result.changes > 0;
}

/** Get a specific member's role in a project. */
export function getProjectMember(
  projectId: string,
  userId: string,
): ProjectMember | undefined {
  const db = getDb();
  return db.prepare(
    'SELECT * FROM project_members WHERE user_id = ? AND project_id = ?',
  ).get(userId, projectId) as ProjectMember | undefined;
}

/** List all members of a project. */
export function listProjectMembers(projectId: string): ProjectMember[] {
  const db = getDb();
  return db.prepare(
    'SELECT * FROM project_members WHERE project_id = ? ORDER BY created_at',
  ).all(projectId) as ProjectMember[];
}

/**
 * Check if a user has at least the given role in a project.
 * Returns the member record if access is granted, undefined otherwise.
 */
export function checkAccess(
  projectId: string,
  userId: string,
  minRole: ProjectRole,
): ProjectMember | undefined {
  const member = getProjectMember(projectId, userId);
  if (!member) return undefined;
  return roleAtLeast(member.role, minRole) ? member : undefined;
}
