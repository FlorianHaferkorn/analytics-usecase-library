import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { FrameworkOverview } from '@/components/ui/framework-overview';

export default async function DashboardPage() {
  const [kpis, brackets, actions] = await Promise.all([
    loadKpiCatalog().catch(() => []),
    loadAllBrackets().catch(() => []),
    loadAllActionCodes().catch(() => []),
  ]);

  // Compute domain distribution from domain_tag[0]
  const domainMap = new Map<string, number>();
  kpis.forEach((k) => {
    const d = k.domain_tag?.[0] ?? 'other';
    domainMap.set(d, (domainMap.get(d) ?? 0) + 1);
  });
  const domains = Array.from(domainMap).map(([name, count], i) => ({
    name,
    count,
    hue: ({ revenue: 250, growth: 150, product: 310, retention: 30, operations: 130 } as Record<string, number>)[name] ?? 200 + i * 50,
  }));

  // Derive status counts from metadata_quality.completeness_score
  const certified = kpis.filter((k) => (k.metadata_quality?.completeness_score ?? 0) >= 0.8).length;
  const inReview = kpis.filter((k) => {
    const s = k.metadata_quality?.completeness_score ?? 0;
    return s >= 0.5 && s < 0.8;
  }).length;

  const stats = {
    kpiCount: kpis.length,
    bracketCount: brackets.length,
    actionCount: actions.length,
    pendingReviews: inReview,
    certified,
    inReview,
    totalDomains: domains.length,
  };

  // Top 4 KPIs for key metrics row — take first 4 from catalog
  const topKpis = kpis.slice(0, 4).map((k) => ({
    id: k.kpi_id,
    name: k.kpi_key.replace(/_/g, ' '),
    ref: k.kpi_id,
    unit: k.business?.unit_format ?? '',
    domain: k.domain_tag?.[0] ?? '',
  }));

  return <FrameworkOverview stats={stats} domains={domains} topKpis={topKpis} />;
}
