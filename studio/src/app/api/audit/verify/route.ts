/**
 * Audit Verify API — check integrity of the audit hash chain.
 *
 * GET /api/audit/verify?projectId=default
 */

import { verifyChain } from '@/lib/db/audit-chain';
import { requireAuth } from '@/lib/auth/session';
import { apiSuccess } from '@/lib/api/response';

export async function GET(request: Request) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const { searchParams } = new URL(request.url);
  const projectId = searchParams.get('projectId') ?? 'default';

  const result = verifyChain(projectId);
  return apiSuccess(result);
}
