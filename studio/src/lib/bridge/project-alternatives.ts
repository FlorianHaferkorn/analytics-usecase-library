import 'server-only';

import { execFile } from 'node:child_process';
import { isAbsolute, join, resolve } from 'node:path';
import type { PackageRepositoryResult } from './project-package-repository';

export interface SetDelta { added: string[]; removed: string[]; unchanged: string[] }
export interface MapDelta { added: string[]; removed: string[]; changed: string[] }
export interface Effort { value: number | null; unit: string; provenance: string }
export interface TopologyRow { domain_ref: string; environment: string; state: string; workspace_refs: string[] }

/** Read-only comparison produced by tooling/superversion/project_package/alternative_impact.py. */
export interface AlternativeImpact {
  schema_version: string;
  project_ref: string;
  baseline_revision_hash: string;
  decision_ref: string;
  baseline_option_ref: string;
  alternative_option_ref: string;
  status: 'impact_ready' | 'blocked';
  blockers: string[];
  impacts: {
    architecture: { environments: SetDelta };
    plan: {
      work_packages: Record<string, { before: { role_refs: string[]; effort: Effort } | null; after: { role_refs: string[]; effort: Effort } | null }>;
      tasks: Record<string, { before: string[] | null; after: string[] | null }>;
    };
    staffing: { role_demand: SetDelta; effort_totals: { before: Record<string, number>; after: Record<string, number> }; named_staffing_or_cost_evaluated: false };
    topology: { baseline: TopologyRow[]; alternative: TopologyRow[] };
    manifests: MapDelta;
    tests: {
      decision_impact_checks: { before: Array<{ rule_id: string; checks: string[] }>; after: Array<{ rule_id: string; checks: string[] }> };
      lane_acceptance: { before: Record<string, string[]>; after: Record<string, string[]> };
      execution_obligations: SetDelta;
    };
  };
  obligations: Array<{ id: string; detail: string }>;
  baseline_unchanged: true;
  hypothetical: true;
  approval_granted: false;
  release_granted: false;
  tenant_actions_performed: false;
  limitations: string[];
  impact_sha256: string;
}

const IDENTIFIER = /^[a-z][a-z0-9_]{0,63}$/;

/** Python owns rule evaluation and the baseline fingerprint; this seam only transports. */
export function projectAlternativeImpact(
  projectId: string, revision: string, decisionRef: string, optionRef: string,
): Promise<PackageRepositoryResult<AlternativeImpact>> {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(projectId) || !/^[a-f0-9]{64}$/.test(revision)
    || !IDENTIFIER.test(decisionRef) || !IDENTIFIER.test(optionRef)) {
    return Promise.resolve({ available: true, ok: false, status: 422, error: 'Invalid project, revision, decision or option' });
  }
  const root = process.env.ALUCA_REPO_ROOT || (process.env.NODE_ENV === 'test' ? resolve(process.cwd(), '..') : undefined);
  if (!root) return Promise.resolve({ available: false, ok: false, status: 503, error: 'Alternative comparison is not configured' });
  const configured = process.env.STUDIO_PACKAGE_DATA_ROOT;
  const dataRoot = configured ? (isAbsolute(configured) ? configured : resolve(process.cwd(), configured)) : join(process.cwd(), 'data', 'project-packages');
  const python = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  const args = [
    ...(!process.env.SUPERVERSION_PYTHON && process.platform === 'win32' ? ['-3'] : []),
    '-m', 'tooling.superversion.project_package.alternative_impact',
    '--repository', join(dataRoot, 'repositories', projectId),
    '--schemas', join(root, 'tooling', 'generator', 'schemas'),
  ];
  const input = { project_ref: projectId, revision_hash: revision, decision_ref: decisionRef, option_ref: optionRef };
  return new Promise(accept => {
    const child = execFile(python, args, { cwd: root, timeout: 60_000, maxBuffer: 8 * 1024 * 1024, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }, (error, stdout) => {
      try {
        const result = JSON.parse(stdout) as { ok: boolean; value?: AlternativeImpact; error?: string; status?: number };
        if (!error && result.ok && result.value) accept({ available: true, ok: true, value: result.value });
        else accept({ available: true, ok: false, status: result.status || 409, error: result.error || 'Comparison could not be completed.' });
      } catch {
        accept({ available: false, ok: false, status: 503, error: 'Alternative comparison did not return a valid result' });
      }
    });
    child.stdin?.on('error', () => { /* The process callback handles failed startup. */ });
    child.stdin?.end(JSON.stringify(input));
  });
}
