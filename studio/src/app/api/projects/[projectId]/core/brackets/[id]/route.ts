/**
 * Tenant-scoped bracket detail.
 *
 * Enforces project membership explicitly before delegating to the canonical
 * handler so tenant isolation is deterministic.
 */
import { NextRequest } from 'next/server';
import { enforceProjectAccess } from '@/lib/auth/enforce-project-access';
import { GET as coreGET, PUT as corePUT } from '@/app/api/core/brackets/[id]/route';

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
