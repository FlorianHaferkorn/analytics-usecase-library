import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadAllSpines } from '@/lib/core/spine-loader';
import { SimulatorClient } from '@/app/(studio)/simulator/simulator-client';
import { PendingDraftBanner } from '@/components/ui/pending-draft-banner';

export default async function ComposePage() {
  const [brackets, spines] = await Promise.all([
    loadAllBrackets(),
    loadAllSpines().catch(() => []),
  ]);

  const bracketSummaries = brackets.map((b) => ({
    id: b.id,
    title: b.title,
    domain: b.domain,
    formula: b.value_driver_model.formula,
    impactDirection: b.value_driver_model.impact_direction,
    primaryDriver: b.value_driver_model.primary_driver,
    strategicKpiId: b.orchestration.strategic_kpi_id,
    influencingKpiIds: b.orchestration.influencing_kpi_ids,
    impactLogic: b.value_driver_model.impact_logic ?? '',
  }));

  return (
    <>
      <PendingDraftBanner />
      <SimulatorClient brackets={bracketSummaries} spines={spines} />
    </>
  );
}
