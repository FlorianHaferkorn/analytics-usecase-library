/**
 * Project Membership Lookup — Node.js runtime only.
 *
 * This module uses better-sqlite3 and must NOT be imported in Edge contexts.
 * It is loaded via dynamic import() inside the NextAuth JWT callback so that
 * Turbopack/webpack cannot statically include it in the Edge middleware bundle.
 */

import { getDb } from '@/lib/db/sqlite';
import { findOrCreateUser } from '@/lib/db/user-repo';
import { addProjectMember, getProjectMember } from '@/lib/db/rbac-repo';
import type { ProjectMembership } from './config';

/**
 * Return the list of project memberships for a given user email.
 * Returns an empty array if the user does not exist or on any error.
 */
export async function lookupProjectMemberships(email: string): Promise<ProjectMembership[]> {
  try {
    const db = getDb();
    const userRow = db
      .prepare('SELECT id FROM users WHERE email = ?')
      .get(email) as { id: string } | undefined;

    if (!userRow) return [];

    const rows = db
      .prepare('SELECT project_id, role FROM project_members WHERE user_id = ?')
      .all(userRow.id) as Array<{ project_id: string; role: string }>;

    return rows.map((r) => ({ projectId: r.project_id, role: r.role }));
  } catch {
    return [];
  }
}

/** The demo identity of the development-only Credentials provider. */
export const DEMO_EMAIL = 'demo@aurora-group.eu';

/**
 * Give the demo user viewer access to the 'default' project (17.10.2026).
 *
 * RBAC (ADR-0014) grants project access only through a project_members row or the
 * org fallback. The demo user is auto-provisioned without either, so every
 * project route answered 403 for it. Seeds exactly one row, never outside
 * development, never for another email, and never downgrades an existing role.
 */
export async function ensureDemoMembership(email: string): Promise<void> {
  if (process.env.NODE_ENV === 'production' || email !== DEMO_EMAIL) return;
  const user = findOrCreateUser(email, email.split('@')[0]);
  if (!getProjectMember('default', user.id)) addProjectMember('default', user.id, 'viewer');
}
