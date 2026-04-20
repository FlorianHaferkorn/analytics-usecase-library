import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { SimulatorClient } from '@/app/(studio)/simulator/simulator-client';

export default async function ComposePage() {
  const brackets = await loadAllBrackets();

  const bracketSummaries = brackets.map((b) => ({
    id: b.id,
    title: b.title,
    domain: b.domain,
    formula: b.value_driver_model.formula,
    impactDirection: b.value_driver_model.impact_direction,
    primaryDriver: b.value_driver_model.primary_driver,
    strategicKpiId: b.orchestration.strategic_kpi_id,
    influencingKpiIds: b.orchestration.influencing_kpi_ids,
  }));

  return <SimulatorClient brackets={bracketSummaries} />;
}
