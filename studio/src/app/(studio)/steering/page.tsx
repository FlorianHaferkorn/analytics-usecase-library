import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { SteeringHubClient } from './steering-hub-client';

export default async function SteeringPage() {
  const [brackets, actions] = await Promise.all([
    loadAllBrackets(),
    loadAllActionCodes(),
  ]);

  // Build action details map for the flow
  const actionDetails: Array<[string, { name: string; status: string; domain: string; triggerKpis: string[] }]> =
    actions.map((a) => [
      a.id,
      {
        name: a.name,
        status: a.status,
        domain: a.owner_domain,
        triggerKpis: a.kpis.trigger_kpis,
      },
    ]);

  // Serialize brackets for the client
  const bracketData = brackets.map((b) => ({
    id: b.id,
    title: b.title,
    domain: b.domain,
    strategicKpiId: b.orchestration.strategic_kpi_id,
    impactDirection: b.value_driver_model.impact_direction,
    influencingKpiIds: b.orchestration.influencing_kpi_ids,
    actionCodeIds: b.orchestration.action_code_ids,
  }));

  return (
    <SteeringHubClient
      strategyAnchor="Profitable growth through margin quality, cash resilience & operational excellence"
      brackets={bracketData}
      actionDetails={actionDetails}
    />
  );
}
