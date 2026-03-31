import { loadAllSpines } from '@/lib/core/spine-loader';
import { apiSuccess } from '@/lib/api/response';

export async function GET() {
  const spines = await loadAllSpines();
  return apiSuccess(spines);
}
