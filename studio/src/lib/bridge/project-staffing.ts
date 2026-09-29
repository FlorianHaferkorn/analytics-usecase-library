import 'server-only';

import { execFile } from 'node:child_process';
import { isAbsolute, join, resolve } from 'node:path';
import type { PackageRepositoryResult } from './project-package-repository';

export interface StaffingClass {
  rate_class: string; hours: number; weekly_capacity: number; weeks: number; earliest_full_team: string | null;
  people: Array<{ name: string; hours: number; hours_per_week: number }>;
}
export interface StaffingSide {
  classes: StaffingClass[];
  gaps: Array<{ rate_class: string; hours: number; detail: string }>;
  weeks_in_parallel: number;
  people: string[];
}
/** Private named staffing from tooling/superversion/project_package/staffing.py. Personal data, never persisted. */
export interface StaffingResult {
  schema_version: string;
  project_ref: string;
  baseline_revision_hash: string;
  decision_ref: string;
  alternative_option_ref: string;
  status: 'evaluated' | 'not_checked' | 'findings';
  personal_data: boolean;
  persist: false;
  roster_fingerprint_sha256?: string;
  reason?: string;
  findings?: string[];
  baseline?: StaffingSide;
  alternative?: StaffingSide;
  delta?: { weeks_in_parallel: { before: number; after: number }; people_no_longer_needed: string[]; people_newly_needed: string[]; new_gaps: string[] };
  limitations?: string[];
}

const IDENTIFIER = /^[a-z][a-z0-9_]{0,63}$/;

/** Python reads the tenant price canon through PREIS_KANON_MANDANTEN_DIR on this host. */
export function projectStaffing(
  projectId: string, revision: string, decisionRef: string, optionRef: string,
): Promise<PackageRepositoryResult<StaffingResult>> {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(projectId) || !/^[a-f0-9]{64}$/.test(revision) || !IDENTIFIER.test(decisionRef) || !IDENTIFIER.test(optionRef)) {
    return Promise.resolve({ available: true, ok: false, status: 422, error: 'Invalid project, revision, decision or option' });
  }
  const root = process.env.ALUCA_REPO_ROOT || (process.env.NODE_ENV === 'test' ? resolve(process.cwd(), '..') : undefined);
  if (!root) return Promise.resolve({ available: false, ok: false, status: 503, error: 'Staffing is not configured' });
  const configured = process.env.STUDIO_PACKAGE_DATA_ROOT;
  const dataRoot = configured ? (isAbsolute(configured) ? configured : resolve(process.cwd(), configured)) : join(process.cwd(), 'data', 'project-packages');
  const python = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  const args = [
    ...(!process.env.SUPERVERSION_PYTHON && process.platform === 'win32' ? ['-3'] : []),
    '-m', 'tooling.superversion.project_package.staffing',
    '--repository', join(dataRoot, 'repositories', projectId),
    '--schemas', join(root, 'tooling', 'generator', 'schemas'),
  ];
  const input = { project_ref: projectId, revision_hash: revision, decision_ref: decisionRef, option_ref: optionRef };
  return new Promise(accept => {
    const child = execFile(python, args, { cwd: root, timeout: 90_000, maxBuffer: 8 * 1024 * 1024, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }, (error, stdout) => {
      try {
        const result = JSON.parse(stdout) as { ok: boolean; value?: StaffingResult; error?: string; status?: number };
        if (!error && result.ok && result.value) accept({ available: true, ok: true, value: result.value });
        else accept({ available: true, ok: false, status: result.status || 409, error: result.error || 'Staffing could not be completed.' });
      } catch {
        accept({ available: false, ok: false, status: 503, error: 'Staffing did not return a valid result' });
      }
    });
    child.stdin?.on('error', () => { /* The process callback handles failed startup. */ });
    child.stdin?.end(JSON.stringify(input));
  });
}
