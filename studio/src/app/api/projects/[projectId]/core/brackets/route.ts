/**
 * Tenant-scoped bracket list/create.
 *
 * This route enforces project membership explicitly before delegating to
 * the canonical handler. (E2E tests rely on deterministic 403 behavior.)
 */
import { enforceProjectAccess } from '@/lib/auth/enforce-project-access';
import { GET as coreGET, POST as corePOST } from '@/app/api/core/brackets/route';

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
