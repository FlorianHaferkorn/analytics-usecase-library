import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';
<<<<<<< HEAD
import { parse } from 'yaml';
=======
>>>>>>> claude/implement-execution-plan-bZbSq
import { parseYaml } from '@/lib/core/yaml-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { loadKpiMap } from '@/lib/core/catalog-loader';
import { getProject } from '@/lib/db/project-repo';
<<<<<<< HEAD
import { BlueprintClient } from './blueprint-client';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';

const CORE_USECASES_DIR = join(process.cwd(), '..', 'core', 'usecases', 'core');
const GOLDEN_20_PATH = join(process.cwd(), '..', 'core', 'kpi_catalog', 'golden_20.yaml');
=======
import { SteeringHubClient } from '@/app/(studio)/steering/steering-hub-client';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';

const CORE_USECASES_DIR = join(process.cwd(), '..', 'core', 'usecases', 'core');
>>>>>>> claude/implement-execution-plan-bZbSq
const FALLBACK_ANCHOR = 'Profitable growth through margin quality, cash resilience & operational excellence';

async function loadBracketsWithYaml() {
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

<<<<<<< HEAD
async function loadGolden20Ids(): Promise<string[]> {
  try {
    const raw = await readFile(GOLDEN_20_PATH, 'utf-8');
    const data = parse(raw) as Record<string, unknown>;
    const kpiList = (data?.kpi_ids ?? []) as Array<{ id: string }>;
    return kpiList.map((k) => k.id).filter(Boolean);
  } catch {
    return [];
  }
}

=======
>>>>>>> claude/implement-execution-plan-bZbSq
export default async function BlueprintPage({
  searchParams,
}: {
  searchParams?: Promise<{ draftId?: string; draftYaml?: string }>;
}) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
<<<<<<< HEAD
  const [{ brackets, yamls: bracketYamls }, actions, kpiMap, golden20Ids] = await Promise.all([
    loadBracketsWithYaml(),
    loadAllActionCodes(),
    loadKpiMap(),
    loadGolden20Ids(),
=======
  const [{ brackets, yamls: bracketYamls }, actions, kpiMap] = await Promise.all([
    loadBracketsWithYaml(),
    loadAllActionCodes(),
    loadKpiMap(),
>>>>>>> claude/implement-execution-plan-bZbSq
  ]);

  const kpiNames: Record<string, string> = {};
  for (const [id, kpi] of kpiMap) {
    kpiNames[id] = kpi.kpi_key || id;
  }

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
    id: string; title: string; domain: string; strategicKpiId: string;
    impactDirection: string; influencingKpiIds: string[]; actionCodeIds: string[];
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
<<<<<<< HEAD
    <BlueprintClient
=======
    <SteeringHubClient
>>>>>>> claude/implement-execution-plan-bZbSq
      strategyAnchor={strategyAnchor}
      brackets={draftBracketData ? [draftBracketData, ...bracketData] : bracketData}
      actionDetails={actionDetails}
      bracketYamls={draftBracketData && draftYaml ? { [draftBracketData.id]: draftYaml, ...bracketYamls } : bracketYamls}
      kpiNames={kpiNames}
      initialSelectedBracket={draftBracketData?.id ?? null}
      draftBracketId={draftBracketData?.id ?? null}
<<<<<<< HEAD
      golden20Ids={golden20Ids}
=======
>>>>>>> claude/implement-execution-plan-bZbSq
    />
  );
}
