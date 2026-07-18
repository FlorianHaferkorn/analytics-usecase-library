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
import { getProject } from '@/lib/db/project-repo';
import type { ProjectMember, ProjectRole } from '@/lib/auth/rbac-types';
import { roleAtLeast } from '@/lib/auth/rbac-types';
import { effectiveRole } from './rebac-eval';

/** Resolve access for (project, user) via the in-process ReBAC model.
 * Mirrors rbac-repo.ts::checkAccess's contract exactly. */
export function checkAccessReBAC(
  projectId: string,
  userId: string,
  minRole: ProjectRole,
): ProjectMember | undefined {
  // Stage 1 — an explicit project_members row decides on its own (override, no merge);
  // the org is irrelevant, so skip the org lookups entirely in that case. Raw SQL here
  // (not getProjectMember) deliberately avoids an import cycle rbac-repo <-> rebac-backend.
  const explicit = getDb()
    .prepare('SELECT role, created_at FROM project_members WHERE user_id = ? AND project_id = ?')
    .get(userId, projectId) as { role: ProjectRole; created_at: string } | undefined;
  if (explicit) {
    if (!roleAtLeast(explicit.role, minRole)) return undefined;
    return { user_id: userId, project_id: projectId, role: explicit.role, created_at: explicit.created_at };
  }

  // Stage 2 — no explicit row: org-derived fallback, only when the project belongs to
  // an org the user is a member of. The model (rebac-eval) resolves the fallback level
  // (owner/admin -> admin, member -> viewer, no editor path).
  const orgId = getProject(projectId)?.org_id ?? null;
  const orgMember = orgId ? getOrgMember(orgId, userId) : undefined;
  if (!orgMember) return undefined;

  const role = effectiveRole({ projectHasOrg: true, orgRole: orgMember.org_role, projectExplicit: null });
  if (role === null || !roleAtLeast(role, minRole)) return undefined;
  return { user_id: userId, project_id: projectId, role, created_at: orgMember.created_at };
}
