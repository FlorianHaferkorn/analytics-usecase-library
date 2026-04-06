import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';
import { parseYaml } from '@/lib/core/yaml-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { getProject } from '@/lib/db/project-repo';
import { SteeringHubClient } from './steering-hub-client';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';

const CORE_USECASES_DIR = join(process.cwd(), '..', 'core', 'usecases', 'core');

/** Load all brackets and their raw YAML in a single pass. */
async function loadBracketsWithYaml(): Promise<{
  brackets: UseCaseBracketV20Lean[];
  yamls: Record<string, string>;
}> {
  const dirs = await readdir(CORE_USECASES_DIR);
  const brackets: UseCaseBracketV20Lean[] = [];
  const yamls: Record<string, string> = {};

  const results = await Promise.all(
    dirs.sort().map(async (dir) => {
      const bracketPath = join(CORE_USECASES_DIR, dir, 'UseCase_Bracket.yaml');
      try {
        const raw = await readFile(bracketPath, 'utf-8');
        const parsed = parseYaml<UseCaseBracketV20Lean>(raw);
        const id = dir.split('_')[0];
        return { parsed, raw, id };
      } catch {
        return null;
      }
    })
  );

  for (const r of results) {
    if (r) {
      brackets.push(r.parsed);
      yamls[r.id] = r.raw;
    }
  }

  return { brackets, yamls };
}

const FALLBACK_ANCHOR = 'Profitable growth through margin quality, cash resilience & operational excellence';

export default async function SteeringPage({
  searchParams,
}: {
  searchParams?: Promise<{ draftId?: string; draftYaml?: string }>;
}) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const [{ brackets, yamls: bracketYamls }, actions] = await Promise.all([
    loadBracketsWithYaml(),
    loadAllActionCodes(),
  ]);

  const defaultProject = getProject('default');
  const strategyAnchor = defaultProject?.strategy_anchor || FALLBACK_ANCHOR;

  const actionDetails: Array<[string, { name: string; status: string; domain: string; triggerKpis: string[] }]> =
    actions.map((a) => [
      a.id,
      { name: a.name, status: a.status, domain: a.owner_domain, triggerKpis: a.kpis.trigger_kpis },
    ]);

  const bracketData = brackets.map((b) => ({
    id: b.id,
    title: b.title,
    domain: b.domain,
    strategicKpiId: b.orchestration.strategic_kpi_id,
    impactDirection: b.value_driver_model.impact_direction,
    influencingKpiIds: b.orchestration.influencing_kpi_ids,
    actionCodeIds: b.orchestration.action_code_ids,
  }));

  let draftBracketData: {
    id: string;
    title: string;
    domain: string;
    strategicKpiId: string;
    impactDirection: string;
    influencingKpiIds: string[];
    actionCodeIds: string[];
  } | null = null;
  let draftYaml: string | null = null;

  if (resolvedSearchParams?.draftId && resolvedSearchParams?.draftYaml) {
    try {
      draftYaml = decodeURIComponent(resolvedSearchParams.draftYaml);
      const parsedDraft = parseYaml<UseCaseBracketV20Lean>(draftYaml);
      draftBracketData = {
        id: resolvedSearchParams.draftId,
        title: parsedDraft.title,
        domain: parsedDraft.domain,
        strategicKpiId: parsedDraft.orchestration.strategic_kpi_id,
        impactDirection: parsedDraft.value_driver_model.impact_direction,
        influencingKpiIds: parsedDraft.orchestration.influencing_kpi_ids,
        actionCodeIds: parsedDraft.orchestration.action_code_ids,
      };
    } catch {
      draftBracketData = null;
      draftYaml = null;
    }
  }

  return (
    <SteeringHubClient
      strategyAnchor={strategyAnchor}
      brackets={draftBracketData ? [draftBracketData, ...bracketData] : bracketData}
      actionDetails={actionDetails}
      bracketYamls={draftBracketData && draftYaml ? { [draftBracketData.id]: draftYaml, ...bracketYamls } : bracketYamls}
      initialSelectedBracket={draftBracketData?.id ?? null}
      draftBracketId={draftBracketData?.id ?? null}
    />
  );
}
