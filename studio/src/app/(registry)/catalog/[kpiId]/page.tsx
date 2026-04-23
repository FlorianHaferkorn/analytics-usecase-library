import { notFound } from 'next/navigation';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { KpiDetail } from '@/components/registry/kpi-detail';

export default async function KpiDetailPage({
  params,
}: {
  params: Promise<{ kpiId: string }>;
}) {
  const { kpiId } = await params;

  const [kpis, brackets] = await Promise.all([
    loadKpiCatalog().catch(() => []),
    loadAllBrackets().catch(() => []),
  ]);

  const kpi = kpis.find((k) => k.kpi_id === kpiId);
  if (!kpi) notFound();

  // Brackets that reference this KPI via orchestration fields
  const linkedBrackets = brackets.filter((b) => {
    const ids: string[] = [];
    if (b.orchestration) {
      if (b.orchestration.strategic_kpi_id) ids.push(b.orchestration.strategic_kpi_id);
      if (b.orchestration.influencing_kpi_ids) ids.push(...b.orchestration.influencing_kpi_ids);
      if (b.orchestration.supporting_kpi_ids) ids.push(...b.orchestration.supporting_kpi_ids);
    }
    return ids.includes(kpiId);
  });

  return (
    <KpiDetail
      kpi={kpi}
      linkedBrackets={linkedBrackets.map((b) => ({
        id: b.id,
        title: b.title,
        domain: b.domain ?? '',
      }))}
    />
  );
}
