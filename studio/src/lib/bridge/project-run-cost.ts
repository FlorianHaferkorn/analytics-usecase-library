import 'server-only';

import { execFile } from 'node:child_process';
import { isAbsolute, join, resolve } from 'node:path';
import type { PackageRepositoryResult } from './project-package-repository';

export interface RunCostCapacity {
  capacity_id: string; sku: string; billing: 'payg' | 'reservation'; price_basis: string; environments: string[]; per_month: number;
  overage: { enabled: boolean; threshold_source: string; max_per_month: number };
}
export interface RunCostLicences {
  authors: number; viewers: number; production_sku: string | null; viewers_need_pro: boolean; pro_users: number;
  /** Null when the licence list price is not available in the result currency. */
  pro_per_user_month: number | null; per_month: number | null; basis: string;
}
export interface RunCostMonitoringStorage { retained_gb: number; per_gb_month: number | null; per_month: number | null }
export interface RunCostSide {
  currency: 'USD' | 'EUR';
  capacities: RunCostCapacity[];
  capacity_per_month: number;
  licences: RunCostLicences | null;
  monitoring_storage: RunCostMonitoringStorage | null;
  per_month: number;
  /** Derived overage maximum; billed only when used, never part of per_month. */
  overage_ceiling_per_month: number;
  priced_capacities: number;
  unpriced: Array<{ item: string; reason: string }>;
}
/** Result of tooling/superversion/project_package/run_cost_delta.py: public list prices, no tenant values. */
export interface RunCostDelta {
  schema_version: string;
  project_ref: string;
  baseline_revision_hash: string;
  decision_ref: string;
  alternative_option_ref: string;
  status: 'evaluated' | 'not_evaluated';
  reason?: string;
  persist: false;
  currency?: 'USD' | 'EUR';
  region?: string;
  price_basis?: string;
  price_valid_from?: string;
  baseline?: RunCostSide;
  alternative?: RunCostSide;
  delta?: {
    per_month: number; per_year: number; capacity_per_month: number; licence_per_month: number;
    monitoring_storage_per_month: number; overage_ceiling_per_month: number;
    capacities_removed: string[]; capacities_added: string[];
  };
  comparable?: boolean;
  limitations?: string[];
}

const IDENTIFIER = /^[a-z][a-z0-9_]{0,63}$/;

export function projectRunCostDelta(
  projectId: string, revision: string, decisionRef: string, optionRef: string,
): Promise<PackageRepositoryResult<RunCostDelta>> {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(projectId) || !/^[a-f0-9]{64}$/.test(revision) || !IDENTIFIER.test(decisionRef) || !IDENTIFIER.test(optionRef)) {
    return Promise.resolve({ available: true, ok: false, status: 422, error: 'Invalid project, revision, decision or option' });
  }
  const root = process.env.ALUCA_REPO_ROOT || (process.env.NODE_ENV === 'test' ? resolve(process.cwd(), '..') : undefined);
  if (!root) return Promise.resolve({ available: false, ok: false, status: 503, error: 'Run-cost comparison is not configured' });
  const configured = process.env.STUDIO_PACKAGE_DATA_ROOT;
  const dataRoot = configured ? (isAbsolute(configured) ? configured : resolve(process.cwd(), configured)) : join(process.cwd(), 'data', 'project-packages');
  const python = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  const args = [
    ...(!process.env.SUPERVERSION_PYTHON && process.platform === 'win32' ? ['-3'] : []),
    '-m', 'tooling.superversion.project_package.run_cost_delta',
    '--repository', join(dataRoot, 'repositories', projectId),
    '--schemas', join(root, 'tooling', 'generator', 'schemas'),
  ];
  const input = { project_ref: projectId, revision_hash: revision, decision_ref: decisionRef, option_ref: optionRef };
  return new Promise(accept => {
    const child = execFile(python, args, { cwd: root, timeout: 90_000, maxBuffer: 8 * 1024 * 1024, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }, (error, stdout) => {
      try {
        const result = JSON.parse(stdout) as { ok: boolean; value?: RunCostDelta; error?: string; status?: number };
        if (!error && result.ok && result.value) accept({ available: true, ok: true, value: result.value });
        else accept({ available: true, ok: false, status: result.status || 409, error: result.error || 'Run-cost comparison could not be completed.' });
      } catch {
        accept({ available: false, ok: false, status: 503, error: 'Run-cost comparison did not return a valid result' });
      }
    });
    child.stdin?.on('error', () => { /* The process callback handles failed startup. */ });
    child.stdin?.end(JSON.stringify(input));
  });
}
