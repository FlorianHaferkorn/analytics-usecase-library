import { auth } from '@/lib/auth/config';
import { NextResponse } from 'next/server';
import type { ProjectMembership } from '@/lib/auth/config';

// Routes that are intentionally public (no auth required).
const PUBLIC_PATHS = new Set(['/', '/login']);

// Pattern that identifies tenant-scoped API routes.
// e.g. /api/projects/my-project-id/core/brackets
const TENANT_API_RE = /^\/api\/projects\/([^/]+)\//;

// Legacy unscoped API routes that carry optional project context via header.
// When X-Project-Id is present, membership is enforced.
// When absent, the request is allowed through for backward compatibility.
const LEGACY_API_RE = /^\/api\/(?:core|factsheets|governance|health|validate|export|notifications|plugins)\//;

function _getMemberships(req: { auth: unknown }): ProjectMembership[] {
  return (
    ((req.auth as Record<string, unknown>).project_memberships as
      ProjectMembership[] | undefined) ?? []
  );
}

function _projectAccessResponse(): NextResponse {
  return new NextResponse(
    JSON.stringify({ error: 'Forbidden', code: 'PROJECT_ACCESS_DENIED' }),
    { status: 403, headers: { 'Content-Type': 'application/json' } },
  );
}

export default auth((req) => {
  const { pathname } = req.nextUrl;

  // 1. Public routes — allow through without any checks.
  if (PUBLIC_PATHS.has(pathname) || pathname.startsWith('/api/auth')) {
    return NextResponse.next();
  }

  // 2. Authentication gate — redirect to login if not signed in.
  if (!req.auth) {
    const loginUrl = new URL('/login', req.nextUrl.origin);
    loginUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // 3. Tenant membership gate — applies to /api/projects/[projectId]/...
  const tenantMatch = pathname.match(TENANT_API_RE);
  if (tenantMatch) {
    const requestedProjectId = tenantMatch[1];
    const memberships = _getMemberships(req);
    const isMember = memberships.some((m) => m.projectId === requestedProjectId);

    // Graceful fallback: pre-migration JWTs with no memberships may access "default".
    const gracefulFallback = memberships.length === 0 && requestedProjectId === 'default';

    if (!isMember && !gracefulFallback) {
      return _projectAccessResponse();
    }
  }

  // 4. Legacy API project isolation — opt-in via X-Project-Id header.
  //    When the header is present, enforce membership exactly like path-based isolation.
  //    When absent, allow through (backward compatibility for callers without header).
  if (LEGACY_API_RE.test(pathname)) {
    const headerProjectId =
      req.headers.get('X-Project-Id') ??
      req.nextUrl.searchParams.get('projectId') ??
      null;

    if (headerProjectId !== null) {
      const memberships = _getMemberships(req);
      const isMember = memberships.some((m) => m.projectId === headerProjectId);
      const gracefulFallback =
        memberships.length === 0 && headerProjectId === 'default';

      if (!isMember && !gracefulFallback) {
        return _projectAccessResponse();
      }
    }
  }

  return NextResponse.next();
});

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
