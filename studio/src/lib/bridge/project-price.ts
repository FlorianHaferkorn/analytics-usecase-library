import 'server-only';

import { execFile } from 'node:child_process';
import { isAbsolute, join, resolve } from 'node:path';
import type { PackageRepositoryResult } from './project-package-repository';

export interface PriceTotals { cost: number; price_calculated: number; price_rounded: number; list_price: number }
export interface PriceSide {
  packages: Array<{ work_package_ref: string; package_ref: string; hours: number; below_calculation: boolean; status: string } & PriceTotals>;
  totals: PriceTotals;
  priced_packages: number;
  unpriced: Array<{ work_package_ref: string; reason: string }>;
  /** Time-and-material packages: a band from the core (D-576), never part of `totals`. */
  time_and_material?: PriceBandRow[];
  time_and_material_price_band?: [number, number];
}
export interface PriceBandRow {
  work_package_ref: string; package_ref: string; hours_band: [number, number]; blended_rate: number;
  rate_mix: Record<string, number>; rate_mix_source: string; price_band: [number, number]; status: string;
}
/** Private money result of tooling/superversion/project_package/price_delta.py. Never persisted. */
export interface PriceDelta {
  schema_version: string;
  project_ref: string;
  baseline_revision_hash: string;
  decision_ref: string;
  alternative_option_ref: string;
  status: 'evaluated' | 'not_checked' | 'tenant_findings';
  price_values_embedded: boolean;
  persist: false;
  currency?: string;
  tenant_fingerprint_sha256?: string;
  reason?: string;
  findings?: string[];
  baseline?: PriceSide;
  alternative?: PriceSide;
  delta?: PriceTotals & { time_and_material_price_band?: [number, number] };
  comparable?: boolean;
  limitations?: string[];
}

const IDENTIFIER = /^[a-z][a-z0-9_]{0,63}$/;

/** Python reads the tenant price canon through PREIS_KANON_MANDANTEN_DIR on this host. */
export function projectPriceDelta(
  projectId: string, revision: string, decisionRef: string, optionRef: string,
): Promise<PackageRepositoryResult<PriceDelta>> {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(projectId) || !/^[a-f0-9]{64}$/.test(revision) || !IDENTIFIER.test(decisionRef) || !IDENTIFIER.test(optionRef)) {
    return Promise.resolve({ available: true, ok: false, status: 422, error: 'Invalid project, revision, decision or option' });
  }
  const root = process.env.ALUCA_REPO_ROOT || (process.env.NODE_ENV === 'test' ? resolve(process.cwd(), '..') : undefined);
  if (!root) return Promise.resolve({ available: false, ok: false, status: 503, error: 'Price delta is not configured' });
  const configured = process.env.STUDIO_PACKAGE_DATA_ROOT;
  const dataRoot = configured ? (isAbsolute(configured) ? configured : resolve(process.cwd(), configured)) : join(process.cwd(), 'data', 'project-packages');
  const python = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  const args = [
    ...(!process.env.SUPERVERSION_PYTHON && process.platform === 'win32' ? ['-3'] : []),
    '-m', 'tooling.superversion.project_package.price_delta',
    '--repository', join(dataRoot, 'repositories', projectId),
    '--schemas', join(root, 'tooling', 'generator', 'schemas'),
  ];
  const input = { project_ref: projectId, revision_hash: revision, decision_ref: decisionRef, option_ref: optionRef };
  return new Promise(accept => {
    const child = execFile(python, args, { cwd: root, timeout: 90_000, maxBuffer: 8 * 1024 * 1024, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }, (error, stdout) => {
      try {
        const result = JSON.parse(stdout) as { ok: boolean; value?: PriceDelta; error?: string; status?: number };
        if (!error && result.ok && result.value) accept({ available: true, ok: true, value: result.value });
        else accept({ available: true, ok: false, status: result.status || 409, error: result.error || 'Price delta could not be completed.' });
      } catch {
        accept({ available: false, ok: false, status: 503, error: 'Price delta did not return a valid result' });
      }
    });
    child.stdin?.on('error', () => { /* The process callback handles failed startup. */ });
    child.stdin?.end(JSON.stringify(input));
  });
}
