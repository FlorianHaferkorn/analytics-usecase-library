import { loadAllContracts } from '@/lib/core/contract-loader';

export async function GET() {
  const contracts = await loadAllContracts();
  return Response.json(contracts);
}
