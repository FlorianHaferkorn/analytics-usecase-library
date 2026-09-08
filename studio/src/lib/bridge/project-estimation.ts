import 'server-only';
import { execFile } from 'node:child_process';
import { isAbsolute, join, resolve } from 'node:path';
import type { PackageRepositoryResult } from './project-package-repository';

export interface EstimateScenario {
  currency: string; planning_workdays: string; contingency_percent: string;
  people: Array<{id: string; name: string; hours_per_day: string; availability_percent: string}>;
  assignments: Array<{id: string; person_id: string; role: string; effort_hours: string; cost_per_hour: string; sell_per_hour: string; currency: string}>;
}
export interface EstimateResult {
  project_ref: string; revision_hash: string; scenario_sha256: string; currency: string; status: 'scenario_only'; inputs: EstimateScenario;
  totals: {cost: string; revenue: string; contribution: string; margin_percent: string | null; buffered_hours: string; minimum_workdays: string | null};
  people: Array<{id: string; name: string; buffered_hours: string; capacity_hours: string; minimum_workdays: string | null; overallocated: boolean; cost: string; revenue: string}>;
  roles: Array<{role: string; buffered_hours: string; cost: string; revenue: string}>;
  warnings: string[]; limitations: string[];
}

export async function projectEstimation(projectId: string, revision: string, scenario: unknown): Promise<PackageRepositoryResult<EstimateResult>> {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(projectId) || !/^[a-f0-9]{64}$/.test(revision)) return {available:true,ok:false,status:422,error:'Invalid project or revision identifier'};
  const repoRoot = process.env.ALUCA_REPO_ROOT || (process.env.NODE_ENV === 'test' ? resolve(process.cwd(), '..') : undefined);
  if (!repoRoot) return {available:false,ok:false,status:503,error:'Estimate engine unavailable'};
  const configured = process.env.STUDIO_PACKAGE_DATA_ROOT;
  const dataRoot = configured ? (isAbsolute(configured) ? configured : resolve(process.cwd(), configured)) : join(process.cwd(), 'data', 'project-packages');
  const python = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  return new Promise(accept => {
    const child = execFile(python, [...(!process.env.SUPERVERSION_PYTHON && process.platform === 'win32' ? ['-3'] : []),
      '-m','tooling.superversion.project_package.estimation','--repository',join(dataRoot,'repositories',projectId),
      '--schemas',join(repoRoot,'tooling','generator','schemas'),'--project-ref',projectId,'--revision',revision],
    {cwd:repoRoot,timeout:30_000,maxBuffer:8*1024*1024,env:{...process.env,PYTHONIOENCODING:'utf-8'}}, (error, stdout) => {
      try {
        const data = JSON.parse(stdout);
        accept(data.ok && !error && data.value ? {available:true,ok:true,value:data.value} : {available:true,ok:false,status:data.status || 422,error:data.error || 'Estimate calculation failed'});
      } catch { accept({available:false,ok:false,status:503,error:'Estimate engine did not return a valid result'}); }
    });
    child.stdin?.on('error', () => { /* Process callback reports failed launch or calculation. */ });
    child.stdin?.end(JSON.stringify(scenario));
  });
}
