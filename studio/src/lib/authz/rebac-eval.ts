/**
 * In-process ReBAC evaluator (ADR-0016 Option A — self-hosted, no external engine).
 *
 * Pure, dependency-free evaluation of the declarative relations model from
 * docs/architecture/research/authn-authz-rebac-schema.md §2. For a single-instance
 * SaaS at Studio's scale, the model is evaluated in-process over the existing SQLite
 * tables — no OpenFGA service to run. OpenFGA stays an optional swap for scale behind
 * the same AUTHZ_BACKEND seam (see rebac-backend.ts).
 *
 * The one non-additive point (ADR-0014 Festlegung 4): an explicit project row
 * OVERRIDES the org-derived fallback entirely — even downward (an explicit viewer
 * caps an org owner). Expressed here via `!explicitAny` guards, mirroring the
 * `but not` difference operator in the OpenFGA rendering (§3).
 *
 * Logic verified 2026-07-15 against a standalone reference evaluator (9/9 cases,
 * docs/architecture/research/authz-fga-cases.json).
 */

import type { OrgRole, ProjectRole } from '@/lib/auth/rbac-types';

/** The facts the model needs about one (user, project) pair — read from the DB
 * by rebac-backend.ts, kept separate so the model itself stays pure/testable. */
export interface AuthzFacts {
  /** project.org_id != NULL — the project belongs to an org. */
  projectHasOrg: boolean;
  /** The user's role in the project's org, or null if not a member / no org. */
  orgRole: OrgRole | null;
  /** The explicit project_members row for (project, user), or null if none. */
  projectExplicit: ProjectRole | null;
}

export type Permission = 'can_view' | 'can_edit' | 'can_admin';

/** Evaluate the three effective permissions for the given facts. */
export function evaluatePermissions(f: AuthzFacts): Record<Permission, boolean> {
  const adminExplicit = f.projectExplicit === 'admin';
  const editorExplicit = f.projectExplicit === 'editor';
  const viewerExplicit = f.projectExplicit === 'viewer';
  const explicitAny = adminExplicit || editorExplicit || viewerExplicit;

  // org hierarchy: owner => admin => member
  const orgIsAdmin = f.orgRole === 'owner' || f.orgRole === 'admin';
  const orgIsMember = orgIsAdmin || f.orgRole === 'member';

  // org-derived fallback sources (owner/admin -> admin level, member -> view level)
  const orgAdminSrc = f.projectHasOrg && orgIsAdmin;
  const orgViewSrc = f.projectHasOrg && orgIsMember;

  // fallback applies ONLY without an explicit row (the non-additive override)
  const adminFallback = orgAdminSrc && !explicitAny;
  const viewFallback = orgViewSrc && !explicitAny;

  return {
    can_admin: adminExplicit || adminFallback,
    can_edit: editorExplicit || adminExplicit || adminFallback,
    can_view: viewerExplicit || editorExplicit || adminExplicit || viewFallback,
  };
}

/** The highest project role the model grants for these facts, or null for no access. */
export function effectiveRole(f: AuthzFacts): ProjectRole | null {
  const p = evaluatePermissions(f);
  if (p.can_admin) return 'admin';
  if (p.can_edit) return 'editor';
  if (p.can_view) return 'viewer';
  return null;
}
