/**
 * Project Membership Lookup — Node.js runtime only.
 *
 * This module uses better-sqlite3 and must NOT be imported in Edge contexts.
 * It is loaded via dynamic import() inside the NextAuth JWT callback so that
 * Turbopack/webpack cannot statically include it in the Edge middleware bundle.
 */

import { getDb } from '@/lib/db/sqlite';
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
