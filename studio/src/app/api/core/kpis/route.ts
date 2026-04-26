import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { apiSuccess } from '@/lib/api/response';
import { requireAuth } from '@/lib/auth/session';

export async function GET(request: Request) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const { searchParams } = new URL(request.url);
  const domain = searchParams.get('domain');
  const search = searchParams.get('q');

  let kpis = await loadKpiCatalog();

  if (domain) {
    kpis = kpis.filter((k) => (k.domain_tag ?? []).includes(domain));
  }

  if (search) {
    const q = search.toLowerCase();
    kpis = kpis.filter(
      (k) =>
        k.kpi_id.toLowerCase().includes(q) ||
        k.kpi_key.toLowerCase().includes(q) ||
        k.business?.purpose?.toLowerCase().includes(q)
    );
  }

  return apiSuccess({ count: kpis.length, kpis });
}
