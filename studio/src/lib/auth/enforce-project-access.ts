/**
 * Shared project-membership gate for tenant-scoped (`/api/projects/[projectId]/...`)
 * route wrappers.
 *
 * Middleware already enforces this at the edge (see `studio/middleware.ts`,
 * `TENANT_API_RE`), but each wrapper route re-checks explicitly so isolation
 * is deterministic under tests that call the route handler directly. This
 * used to be duplicated verbatim across 4+ wrapper files — kept here once so
 * a change to the graceful-fallback rule can't drift between copies.
 */
import { auth, type ProjectMembership } from '@/lib/auth/config';

function getMemberships(session: unknown): ProjectMembership[] {
  const anySession = session as Record<string, unknown> | null | undefined;
  return (anySession?.project_memberships as ProjectMembership[] | undefined) ?? [];
}

export function projectAccessDeniedResponse(): Response {
  return new Response(JSON.stringify({ error: 'Forbidden', code: 'PROJECT_ACCESS_DENIED' }), {
    status: 403,
    headers: { 'Content-Type': 'application/json' },
  });
}

/**
 * Returns a 403 Response if the current session is authenticated but not a
 * member of `projectId` (and not covered by the pre-migration graceful
 * fallback to 'default'). Returns null to let the caller proceed — including
 * when there is no session at all, so the canonical handler can return its
 * own 401.
 */
export async function enforceProjectAccess(projectId: string): Promise<Response | null> {
  const session = await auth();
  const memberships = getMemberships(session);

  if (!session?.user?.email) return null;

  const isMember = memberships.some((m) => m.projectId === projectId);
  const gracefulFallback = memberships.length === 0 && projectId === 'default';

  if (!isMember && !gracefulFallback) return projectAccessDeniedResponse();
  return null;
}
