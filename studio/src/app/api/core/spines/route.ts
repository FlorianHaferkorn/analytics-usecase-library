import { loadAllSpines } from '@/lib/core/spine-loader';

export async function GET() {
  const spines = await loadAllSpines();
  return Response.json(spines);
}
