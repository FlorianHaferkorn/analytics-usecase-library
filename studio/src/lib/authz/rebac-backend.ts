/**
 * ReBAC AuthZ backend (in-process) — the `rebac` value of AUTHZ_BACKEND.
 *
 * Reads the facts the model needs from the existing SQLite tables and evaluates
 * the declarative model (rebac-eval.ts). Returns the same `ProjectMember | undefined`
 * shape as the imperative `local` path in rbac-repo.ts, so callers are unchanged.
 *
 * No network, no OpenFGA service — self-hosted by construction (Node only). OpenFGA
 * remains an optional swap for scale: a future `fga` backend would implement the same
 * signature via the engine's check() API, reusing the same model (model.fga) and the
 * same test vectors (authz-fga-cases.json).
 */

import { getDb } from '@/lib/db/sqlite';
import { getOrgMember } from '@/lib/db/org-repo';
import type { ProjectMember, ProjectRole } from '@/lib/auth/rbac-types';
import { roleAtLeast } from '@/lib/auth/rbac-types';
import { effectiveRole, type AuthzFacts } from './rebac-eval';

/** Resolve access for (project, user) via the in-process ReBAC model.
 * Mirrors rbac-repo.ts::checkAccess's contract exactly. */
export function checkAccessReBAC(
  projectId: string,
  userId: string,
  minRole: ProjectRole,
): ProjectMember | undefined {
  const db = getDb();

  const project = db
    .prepare('SELECT org_id FROM projects WHERE id = ?')
    .get(projectId) as { org_id: string | null } | undefined;
  const explicit = db
    .prepare('SELECT role, created_at FROM project_members WHERE user_id = ? AND project_id = ?')
    .get(userId, projectId) as { role: ProjectRole; created_at: string } | undefined;

  const orgId = project?.org_id ?? null;
  const orgMember = orgId ? getOrgMember(orgId, userId) : undefined;

  const facts: AuthzFacts = {
    projectHasOrg: orgId !== null,
    orgRole: orgMember?.org_role ?? null,
    projectExplicit: explicit?.role ?? null,
  };

  const role = effectiveRole(facts);
  if (role === null || !roleAtLeast(role, minRole)) return undefined;

  // Same shape as the local path: a real row's created_at when explicit, else the
  // org membership's (synthetic fallback, as resolveOrgFallbackAccess does).
  return {
    user_id: userId,
    project_id: projectId,
    role,
    created_at: explicit?.created_at ?? orgMember?.created_at ?? '',
  };
}
