import { loadAllContracts } from '@/lib/core/contract-loader';
import { apiSuccess } from '@/lib/api/response';
import { requireAuth } from '@/lib/auth/session';

export async function GET() {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const contracts = await loadAllContracts();
  return apiSuccess(contracts);
}
