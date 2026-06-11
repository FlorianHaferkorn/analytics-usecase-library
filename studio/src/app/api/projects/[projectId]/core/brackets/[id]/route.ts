/**
 * Tenant-scoped bracket detail.
 *
 * Enforces project membership explicitly before delegating to the canonical
 * handler so tenant isolation is deterministic.
 */
import { auth, type ProjectMembership } from '@/lib/auth/config';
import { NextRequest } from 'next/server';
import { GET as coreGET, PUT as corePUT } from '@/app/api/core/brackets/[id]/route';

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

  // No session => let canonical handler return 401.
  if (!session?.user?.email) return null;

  const isMember = memberships.some((m) => m.projectId === projectId);
  const gracefulFallback = memberships.length === 0 && projectId === 'default';

  if (!isMember && !gracefulFallback) return projectAccessDeniedResponse();
  return null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ projectId: string; id: string }> },
) {
  const { projectId } = await params;
  const denied = await enforceProjectAccess(projectId);
  if (denied) return denied;
  return coreGET(request, { params });
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ projectId: string; id: string }> },
) {
  const { projectId } = await params;
  const denied = await enforceProjectAccess(projectId);
  if (denied) return denied;
  return corePUT(request, { params });
}
