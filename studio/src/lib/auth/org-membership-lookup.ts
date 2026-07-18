/**
 * Org Membership Lookup — Node.js runtime only (mirrors membership-lookup.ts).
 *
 * Uses better-sqlite3 and must NOT be imported in Edge contexts. Loaded via
 * dynamic import() inside the NextAuth JWT callback (ADR-0014 Festlegung 5).
 */

import { getDb } from '@/lib/db/sqlite';
import type { OrgMembership } from './config';

/** Return the list of org memberships for a given user email. Empty array on any error. */
export async function lookupOrgMemberships(email: string): Promise<OrgMembership[]> {
  try {
    const db = getDb();
    const userRow = db
      .prepare('SELECT id FROM users WHERE email = ?')
      .get(email) as { id: string } | undefined;

    if (!userRow) return [];

    const rows = db
      .prepare('SELECT org_id, org_role FROM org_members WHERE user_id = ?')
      .all(userRow.id) as Array<{ org_id: string; org_role: string }>;

    return rows.map((r) => ({ orgId: r.org_id, role: r.org_role }));
  } catch {
    return [];
  }
}
