/**
 * Tenant-scoped bracket list/create.
 *
 * This route enforces project membership explicitly before delegating to
 * the canonical handler. (E2E tests rely on deterministic 403 behavior.)
 */
import { auth, type ProjectMembership } from '@/lib/auth/config';
import { GET as coreGET, POST as corePOST } from '@/app/api/core/brackets/route';

function projectAccessDeniedResponse(): Response {
  return new Response(JSON.stringify({ error: 'Forbidden', code: 'PROJECT_ACCESS_DENIED' }), {
    status: 403,
    headers: { 'Content-Type': 'application/json' },
  });
}

function getMemberships(session: unknown): ProjectMembership[] {
  const anySession = session as Record<string, unknown> | null | undefined;
  return (anySession?.project_memberships as ProjectMembership[] | undefined) ?? [];
}

async function enforceProjectAccess(projectId: string): Promise<Response | null> {
  const session = await auth();
  const memberships = getMemberships(session);

  // If there is no session, let the canonical handler return 401.
  if (!session?.user?.email) return null;

  const isMember = memberships.some((m) => m.projectId === projectId);
  const gracefulFallback = memberships.length === 0 && projectId === 'default';

  if (!isMember && !gracefulFallback) return projectAccessDeniedResponse();
  return null;
}

export async function GET(request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  const denied = await enforceProjectAccess(projectId);
  if (denied) return denied;
  return coreGET(request);
}

export async function POST(request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  const denied = await enforceProjectAccess(projectId);
  if (denied) return denied;
  return corePOST(request);
}
