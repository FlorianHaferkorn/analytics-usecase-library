'use client';

import { useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import { BlueprintClient } from './blueprint-client';
import { ForgePageSkeleton } from '@/components/forge/forge-page-skeleton';
import { useForgeBootstrapContext } from '@/components/providers/forge-bootstrap-provider';
import { parseYaml } from '@/lib/core/yaml-loader';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';

export function BlueprintPageClient() {
  const { data, loading, error } = useForgeBootstrapContext();
  const searchParams = useSearchParams();

  const actionDetails = useMemo(
    () =>
      (data?.actionDetails ?? []).map(
        (action): [string, { name: string; status: string; domain: string; triggerKpis: string[] }] => [
          action.id,
          {
            name: action.name,
            status: action.status,
            domain: action.domain,
            triggerKpis: action.triggerKpis,
          },
        ],
      ),
    [data?.actionDetails],
  );

  const draftState = useMemo(() => {
    const draftId = searchParams.get('draftId');
    const draftYamlParam = searchParams.get('draftYaml');
    if (!draftId || !draftYamlParam) {
      return { draftBracketData: null, draftYaml: null };
    }

    try {
      const draftYaml = decodeURIComponent(draftYamlParam);
      const parsedDraft = parseYaml<UseCaseBracketV20Lean>(draftYaml);
      return {
        draftYaml,
        draftBracketData: {
          id: draftId,
          title: parsedDraft.title,
          domain: parsedDraft.domain,
          strategicKpiId: parsedDraft.orchestration.strategic_kpi_id,
          impactDirection: parsedDraft.value_driver_model.impact_direction,
          influencingKpiIds: parsedDraft.orchestration.influencing_kpi_ids,
          actionCodeIds: parsedDraft.orchestration.action_code_ids,
        },
      };
    } catch {
      return { draftBracketData: null, draftYaml: null };
    }
  }, [searchParams]);

  if (loading && !data) {
    return <ForgePageSkeleton title="Blueprint" />;
  }

  if (error || !data) {
    return (
      <div style={{ color: 'var(--danger)' }}>
        {error ?? 'Forge data unavailable. Refresh the page or sign in again.'}
      </div>
    );
  }

  const bracketData = data.brackets.map((bracket) => ({
    id: bracket.id,
    title: bracket.title,
    domain: bracket.domain,
    strategicKpiId: bracket.strategicKpiId,
    impactDirection: bracket.impactDirection,
    influencingKpiIds: bracket.influencingKpiIds,
    actionCodeIds: bracket.actionCodeIds,
  }));

  const { draftBracketData, draftYaml } = draftState;

  return (
    <BlueprintClient
      strategyAnchor={data.strategyAnchor}
      brackets={draftBracketData ? [draftBracketData, ...bracketData] : bracketData}
      actionDetails={actionDetails}
      bracketYamls={
        draftBracketData && draftYaml ? { [draftBracketData.id]: draftYaml } : {}
      }
      kpiNames={data.kpiNames}
      actionNames={data.actionNames}
      initialSelectedBracket={draftBracketData?.id ?? null}
      draftBracketId={draftBracketData?.id ?? null}
      golden20Ids={data.golden20Ids}
      spines={data.spines}
    />
  );
}
