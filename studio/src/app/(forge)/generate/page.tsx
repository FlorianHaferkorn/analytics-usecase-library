import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { DeliveryClient } from '@/app/(studio)/delivery/delivery-client';

export default async function GeneratePage() {
  const brackets = await loadAllBrackets();

  const bracketSummaries = brackets.map((b) => ({
    id: b.id,
    title: b.title,
    domain: b.domain,
    kpiCount:
      1 +
      b.orchestration.influencing_kpi_ids.length +
      (b.orchestration.supporting_kpi_ids?.length ?? 0),
    actionCount: b.orchestration.action_code_ids.length,
  }));

  return <DeliveryClient brackets={bracketSummaries} />;
}
