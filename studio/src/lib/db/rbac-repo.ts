/**
 * RBAC Repository — project membership and access control.
 *
 * Each project has members with roles: admin, editor, viewer.
 * The user who creates a project is auto-assigned as admin.
 */

import { getDb } from './sqlite';
import type { ProjectMember, ProjectRole } from '@/lib/auth/rbac-types';
import { roleAtLeast, projectRoleFromOrgRole } from '@/lib/auth/rbac-types';
import { checkOrgAccess } from './org-repo';

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
function removeProjectMember(projectId: string, userId: string): boolean {
  const db = getDb();
  const result = db.prepare(
    'DELETE FROM project_members WHERE user_id = ? AND project_id = ?',
  ).run(userId, projectId);
  return result.changes > 0;
}

/** Get a specific member's role in a project. */
function getProjectMember(
  projectId: string,
  userId: string,
): ProjectMember | undefined {
  const db = getDb();
  return db.prepare(
    'SELECT * FROM project_members WHERE user_id = ? AND project_id = ?',
  ).get(userId, projectId) as ProjectMember | undefined;
}

/** List all members of a project. */
function listProjectMembers(projectId: string): ProjectMember[] {
  const db = getDb();
  return db.prepare(
    'SELECT * FROM project_members WHERE project_id = ? ORDER BY created_at',
  ).all(projectId) as ProjectMember[];
}

/**
 * Check if a user has at least the given role in a project.
 *
 * Two-stage resolution (ADR-0014 Festlegung 4): an explicit project_members row
 * always wins, full stop, regardless of any org role — never merged/upgraded.
 * Only absent an explicit row does an org-derived fallback role apply, and only
 * if the project belongs to an org the user is a member of. No project row and
 * no applicable org membership -> no access, same as before this ADR existed.
 */
export function checkAccess(
  projectId: string,
  userId: string,
  minRole: ProjectRole,
): ProjectMember | undefined {
  const member = getProjectMember(projectId, userId);
  if (member) {
    return roleAtLeast(member.role, minRole) ? member : undefined;
  }
  return resolveOrgFallbackAccess(projectId, userId, minRole);
}

/** Org-role fallback path (ADR-0014 Festlegung 4b) — only reached when no explicit
 * project_members row exists for this (projectId, userId) pair. */
function resolveOrgFallbackAccess(
  projectId: string,
  userId: string,
  minRole: ProjectRole,
): ProjectMember | undefined {
  const db = getDb();
  const project = db.prepare('SELECT org_id FROM projects WHERE id = ?').get(projectId) as { org_id: string | null } | undefined;
  if (!project?.org_id) return undefined;

  const orgMember = checkOrgAccess(project.org_id, userId, 'member');
  if (!orgMember) return undefined;

  const fallbackRole = projectRoleFromOrgRole(orgMember.org_role);
  if (!roleAtLeast(fallbackRole, minRole)) return undefined;

  // Synthetic ProjectMember — not a real project_members row (none exists on
  // this path by construction), just the resolved fallback access level in the
  // same shape callers already expect.
  return { user_id: userId, project_id: projectId, role: fallbackRole, created_at: orgMember.created_at };
}
