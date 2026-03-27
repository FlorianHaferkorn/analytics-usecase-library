import { NextResponse } from 'next/server';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';

export async function GET(request: Request) {
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

  return NextResponse.json({
    count: kpis.length,
    kpis,
  });
}
