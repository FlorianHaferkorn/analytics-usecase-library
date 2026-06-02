import { loadAllActionCodes } from '@/lib/core/action-loader';
import { loadKpiMap } from '@/lib/core/catalog-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { getProject } from '@/lib/db/project-repo';
import type { GoldenThreadData } from '@/components/flow/golden-thread-flow';

const FALLBACK_ANCHOR =
  'Profitable growth through margin quality, cash resilience & operational excellence';

/** Server-side Golden Thread payload for Canvas / Blueprint views. */
export async function buildGoldenThreadData(): Promise<GoldenThreadData> {
  const [brackets, actions, kpiMap] = await Promise.all([
    loadAllBrackets(),
    loadAllActionCodes(),
    loadKpiMap(),
  ]);

  const kpiNames: Record<string, string> = {};
  for (const [id, kpi] of kpiMap) {
    kpiNames[id] = kpi.kpi_key || id;
  }

  let strategyAnchor = FALLBACK_ANCHOR;
  try {
    const defaultProject = getProject('default');
    if (defaultProject?.strategy_anchor) strategyAnchor = defaultProject.strategy_anchor;
  } catch {
    // SQLite may be unavailable during static prerender (e.g. native module mismatch).
  }

  const actionDetails = new Map<
    string,
    { name: string; status: string; domain: string; triggerKpis: string[] }
  >();
  for (const a of actions) {
    actionDetails.set(a.id, {
      name: a.name,
      status: a.status,
      domain: a.owner_domain,
      triggerKpis: a.kpis.trigger_kpis,
    });
  }

  return {
    strategyAnchor,
    brackets: brackets.map((b) => ({
      id: b.id,
      title: b.title,
      domain: b.domain,
      strategicKpiId: b.orchestration.strategic_kpi_id,
      impactDirection: b.value_driver_model.impact_direction,
      influencingKpiIds: b.orchestration.influencing_kpi_ids,
      actionCodeIds: b.orchestration.action_code_ids,
    })),
    actionDetails,
    kpiNames,
  };
}
