import { loadAllContracts } from '@/lib/core/contract-loader';
import { apiSuccess } from '@/lib/api/response';

export async function GET() {
  const contracts = await loadAllContracts();
  return apiSuccess(contracts);
}
