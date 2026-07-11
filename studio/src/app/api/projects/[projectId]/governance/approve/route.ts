/**
 * Tenant-scoped governance approve.
 *
 * This route enforces project membership explicitly before delegating to the
 * canonical handler, and forwards the URL path's projectId as an override —
 * the canonical handler otherwise resolves projectId from body/query, which
 * is a different (spoofable) source than what middleware/this route gate
 * membership on. See bracket_lifecycle composite-PK fix ledger entry.
 */
import { enforceProjectAccess } from '@/lib/auth/enforce-project-access';
import { handleApproveGET, handleApprovePOST } from '@/app/api/governance/approve/route';

export async function GET(request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  const denied = await enforceProjectAccess(projectId);
  if (denied) return denied;
  return handleApproveGET(request, projectId);
}

export async function POST(request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  const denied = await enforceProjectAccess(projectId);
  if (denied) return denied;
  return handleApprovePOST(request, projectId);
}
