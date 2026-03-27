import { readFile, readdir, stat } from 'node:fs/promises';
import { join } from 'node:path';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { SteeringHubClient } from './steering-hub-client';

const CORE_USECASES_DIR = join(process.cwd(), '..', 'core', 'usecases', 'core');

async function loadBracketYamls(): Promise<Record<string, string>> {
  const yamls: Record<string, string> = {};
  try {
    const dirs = await readdir(CORE_USECASES_DIR);
    for (const dir of dirs) {
      const bracketPath = join(CORE_USECASES_DIR, dir, 'UseCase_Bracket.yaml');
      try {
        const s = await stat(bracketPath);
        if (!s.isFile()) continue;
        const raw = await readFile(bracketPath, 'utf-8');
        // Extract ID from filename pattern: COM-001_*
        const id = dir.split('_')[0];
        yamls[id] = raw;
      } catch { /* skip */ }
    }
  } catch { /* skip */ }
  return yamls;
}

export default async function SteeringPage() {
  const [brackets, actions, bracketYamls] = await Promise.all([
    loadAllBrackets(),
    loadAllActionCodes(),
    loadBracketYamls(),
  ]);

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

  return (
    <SteeringHubClient
      strategyAnchor="Profitable growth through margin quality, cash resilience & operational excellence"
      brackets={bracketData}
      actionDetails={actionDetails}
      bracketYamls={bracketYamls}
    />
  );
}
