import { cache } from 'react';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadKpiMap } from '@/lib/core/catalog-loader';
import { GOLDEN_20_IDS } from '@/lib/core/golden20';
import { loadAllSpines } from '@/lib/core/spine-loader';
import { loadAuroraSnapshot } from '@/lib/aurora/kpi-snapshot';
import type { AuroraKpiValue } from '@/lib/aurora/kpi-snapshot';
import type { DecisionSpine } from '@/lib/schemas/decision-spine';
import { cached, FORGE_CACHE_TTL_MS, invalidateCache } from './memory-cache';

const FALLBACK_ANCHOR =
  'Profitable growth through margin quality, cash resilience & operational excellence';

export interface ForgeBracketSummary {
  id: string;
  title: string;
  domain: string;
  strategicKpiId: string;
  impactDirection: 'maximize' | 'minimize';
  influencingKpiIds: string[];
  supportingKpiIds: string[];
  actionCodeIds: string[];
  formula: string;
  primaryDriver: string;
  impactLogic: string;
}

export interface ForgeActionDetail {
  id: string;
  name: string;
  status: string;
  domain: string;
  triggerKpis: string[];
}

export interface ForgeBootstrapPayload {
  strategyAnchor: string;
  brackets: ForgeBracketSummary[];
  actionDetails: ForgeActionDetail[];
  kpiNames: Record<string, string>;
  /** Catalog `business.unit_format` by KPI ID — the unit no longer lives in the ID (D-594). */
  kpiUnitFormats: Record<string, string>;
  actionNames: Record<string, string>;
  spines: DecisionSpine[];
  auroraKpis: Record<string, AuroraKpiValue> | null;
  auroraLinked: boolean;
  golden20Ids: string[];
}

async function buildForgeBootstrapPayload(): Promise<ForgeBootstrapPayload> {
  const [brackets, actions, kpiMap, spines, auroraSnapshot] = await Promise.all([
    loadAllBrackets(),
    loadAllActionCodes(),
    loadKpiMap(),
    loadAllSpines().catch(() => [] as DecisionSpine[]),
    Promise.resolve(loadAuroraSnapshot()),
  ]);

  const kpiNames: Record<string, string> = {};
  const kpiUnitFormats: Record<string, string> = {};
  for (const [id, kpi] of kpiMap) {
    kpiNames[id] = kpi.kpi_key || id;
    if (kpi.business?.unit_format) kpiUnitFormats[id] = kpi.business.unit_format;
  }

  const actionNames: Record<string, string> = {};
  const actionDetails: ForgeActionDetail[] = actions.map((action) => {
    actionNames[action.id] = action.name;
    return {
      id: action.id,
      name: action.name,
      status: action.status,
      domain: action.owner_domain,
      triggerKpis: action.kpis.trigger_kpis,
    };
  });

  // This is a reusable library example, not mutable customer project metadata.
  const strategyAnchor = FALLBACK_ANCHOR;

  return {
    strategyAnchor,
    brackets: brackets.map((bracket) => ({
      id: bracket.id,
      title: bracket.title,
      domain: bracket.domain,
      strategicKpiId: bracket.orchestration.strategic_kpi_id,
      impactDirection: bracket.value_driver_model.impact_direction as 'maximize' | 'minimize',
      influencingKpiIds: bracket.orchestration.influencing_kpi_ids,
      supportingKpiIds: bracket.orchestration.supporting_kpi_ids ?? [],
      actionCodeIds: bracket.orchestration.action_code_ids,
      formula: bracket.value_driver_model.formula,
      primaryDriver: bracket.value_driver_model.primary_driver ?? '',
      impactLogic: bracket.value_driver_model.impact_logic ?? '',
    })),
    actionDetails,
    kpiNames,
    kpiUnitFormats,
    actionNames,
    spines,
    auroraKpis: auroraSnapshot?.kpis ?? null,
    auroraLinked: Boolean(auroraSnapshot),
    golden20Ids: [...GOLDEN_20_IDS],
  };
}

export const loadForgeBootstrap = cache(async (): Promise<ForgeBootstrapPayload> => {
  return cached('forge-bootstrap-v1', FORGE_CACHE_TTL_MS, buildForgeBootstrapPayload);
});

export function invalidateForgeBootstrapCache(): void {
  invalidateCache('forge-bootstrap');
}
