import { auth } from '@/lib/auth/config';
import { NextResponse } from 'next/server';
import type { ProjectMembership } from '@/lib/auth/config';

// Routes that are intentionally public (no auth required).
const PUBLIC_PATHS = new Set(['/', '/login']);

// Pattern that identifies tenant-scoped API routes.
// e.g. /api/projects/my-project-id/core/brackets
const TENANT_API_RE = /^\/api\/projects\/([^/]+)\//;

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

  // 3. Tenant membership gate — applies only to /api/projects/[projectId]/...
  const tenantMatch = pathname.match(TENANT_API_RE);
  if (tenantMatch) {
    const requestedProjectId = tenantMatch[1];

    // Read memberships from the JWT.  The JWT callback populates this array at
    // sign-in time.  We fall back to granting access to the "default" project
    // so that users who signed in before this feature was deployed are not
    // immediately locked out (graceful migration).
    const memberships = (
      (req.auth as unknown as Record<string, unknown>).project_memberships as
        ProjectMembership[] | undefined
    ) ?? [];

    const isMember = memberships.some((m) => m.projectId === requestedProjectId);

    // Graceful fallback: if the user has NO memberships at all (pre-migration
    // JWT) AND the requested project is "default", let them through.
    const gracefulFallback = memberships.length === 0 && requestedProjectId === 'default';

    if (!isMember && !gracefulFallback) {
      return new NextResponse(
        JSON.stringify({ error: 'Forbidden', code: 'PROJECT_ACCESS_DENIED' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } },
      );
    }
  }

  return NextResponse.next();
});

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
