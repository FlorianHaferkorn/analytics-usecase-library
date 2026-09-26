import 'server-only';

import { execFile } from 'node:child_process';
import { isAbsolute, join, resolve } from 'node:path';
import type { PackageRepositoryResult } from './project-package-repository';

export interface CommercialGap { id: string; detail: string }
export interface CommercialSide {
  packages: Array<{ work_package_ref: string; package_ref: string; quantities: Record<string, number>; quantity_provenance: Record<string, string>; delivery_band_workdays: [number, number] }>;
  hours_by_canon_role: Record<string, number>;
  window_workdays: { parallel: number; serial: number };
  capacity_notes: string[];
  gaps: CommercialGap[];
}
/** Rate-free result of tooling/superversion/project_package/commercial_impact.py. */
export interface CommercialImpact {
  schema_version: string;
  project_ref: string;
  baseline_revision_hash: string;
  decision_ref: string;
  alternative_option_ref: string;
  status: 'evaluated' | 'not_checked' | 'tenant_findings';
  price_values_embedded: false;
  reason?: string;
  findings?: string[];
  baseline?: CommercialSide;
  alternative?: CommercialSide;
  delta?: { hours_by_canon_role: Record<string, { before: number; after: number }>; window_workdays: { before: { parallel: number; serial: number }; after: { parallel: number; serial: number } }; new_gaps: string[]; resolved_gaps: string[] };
  proposal_assumptions_markdown?: string;
}

/** Same terms as the Python guard. A second check at the seam, not a replacement. */
const FORBIDDEN = /(kostensatz|verkaufssatz|satz_eur|preis|price|rate|marge|margin|risiko|risk|eur\b|_eur|festpreis|selbstkosten|cost_value)/i;
export function findRateField(value: unknown, path = ''): string | null {
  if (Array.isArray(value)) {
    for (const [index, item] of value.entries()) { const hit = findRateField(item, `${path}${index}.`); if (hit) return hit; }
  } else if (value && typeof value === 'object') {
    for (const [key, item] of Object.entries(value)) {
      if (key === 'price_values_embedded') { if (item !== false) return `${path}${key}`; continue; }
      if (FORBIDDEN.test(key)) return `${path}${key}`;
      const hit = findRateField(item, `${path}${key}.`); if (hit) return hit;
    }
  }
  return null;
}

const IDENTIFIER = /^[a-z][a-z0-9_]{0,63}$/;

/** Python reads the tenant price canon through PREIS_KANON_MANDANTEN_DIR on this host. */
export function projectCommercialImpact(
  projectId: string, revision: string, decisionRef: string, optionRef: string,
): Promise<PackageRepositoryResult<CommercialImpact>> {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(projectId) || !/^[a-f0-9]{64}$/.test(revision) || !IDENTIFIER.test(decisionRef) || !IDENTIFIER.test(optionRef)) {
    return Promise.resolve({ available: true, ok: false, status: 422, error: 'Invalid project, revision, decision or option' });
  }
  const root = process.env.ALUCA_REPO_ROOT || (process.env.NODE_ENV === 'test' ? resolve(process.cwd(), '..') : undefined);
  if (!root) return Promise.resolve({ available: false, ok: false, status: 503, error: 'Commercial comparison is not configured' });
  const configured = process.env.STUDIO_PACKAGE_DATA_ROOT;
  const dataRoot = configured ? (isAbsolute(configured) ? configured : resolve(process.cwd(), configured)) : join(process.cwd(), 'data', 'project-packages');
  const python = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  const args = [
    ...(!process.env.SUPERVERSION_PYTHON && process.platform === 'win32' ? ['-3'] : []),
    '-m', 'tooling.superversion.project_package.commercial_impact',
    '--repository', join(dataRoot, 'repositories', projectId),
    '--schemas', join(root, 'tooling', 'generator', 'schemas'),
    '--assumptions', 'alternative',
  ];
  const input = { project_ref: projectId, revision_hash: revision, decision_ref: decisionRef, option_ref: optionRef };
  return new Promise(accept => {
    const child = execFile(python, args, { cwd: root, timeout: 90_000, maxBuffer: 8 * 1024 * 1024, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }, (error, stdout) => {
      try {
        const result = JSON.parse(stdout) as { ok: boolean; value?: CommercialImpact; error?: string; status?: number };
        if (!error && result.ok && result.value) accept({ available: true, ok: true, value: result.value });
        else accept({ available: true, ok: false, status: result.status || 409, error: result.error || 'Commercial comparison could not be completed.' });
      } catch {
        accept({ available: false, ok: false, status: 503, error: 'Commercial comparison did not return a valid result' });
      }
    });
    child.stdin?.on('error', () => { /* The process callback handles failed startup. */ });
    child.stdin?.end(JSON.stringify(input));
  });
}
