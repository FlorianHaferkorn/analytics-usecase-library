/**
 * Server-side KPI Search API — paginated, filterable.
 *
 * GET /api/core/kpis/search?q=margin&domain=Finance&limit=30&offset=0
 */

import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { apiSuccess } from '@/lib/api/response';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get('q')?.toLowerCase() ?? '';
  const domain = searchParams.get('domain');
  const limit = Math.min(Number(searchParams.get('limit') ?? '30'), 100);
  const offset = Number(searchParams.get('offset') ?? '0');

  let kpis = await loadKpiCatalog();

  if (domain) {
    kpis = kpis.filter((k) => (k.domain_tag ?? []).includes(domain));
  }

  if (q) {
    kpis = kpis.filter(
      (k) =>
        k.kpi_id.toLowerCase().includes(q) ||
        k.kpi_key.toLowerCase().includes(q) ||
        k.business?.purpose?.toLowerCase().includes(q),
    );
  }

  const total = kpis.length;
  const page = kpis.slice(offset, offset + limit);

  return apiSuccess({ kpis: page, total, limit, offset });
}
