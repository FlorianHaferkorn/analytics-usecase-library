import 'server-only';
import { execFile } from 'node:child_process';
import { isAbsolute, join, resolve } from 'node:path';
import type { PackageRepositoryResult } from './project-package-repository';
import type { ArchitectureTarget } from './project-architecture';
export type AutomationTarget = ArchitectureTarget | 'fabric_item_requests' | 'proposal_assumptions';

export interface AutomationRun {
  run_id: string; created_at: string; actor: string; project_ref: string; revision_hash: string;
  status: string; scope: string; delivery_complete: false; apply_ready: false;
  tenant_actions_performed: false; files: Array<{path: string; sha256: string}>;
  limitations: string[]; report_sha256: string;
}
export interface ProjectAutomation {
  schema_version: string; project_ref: string; revision_hash: string;
  stages: Array<{id: string; label: string; status: 'ready' | 'blocked' | 'recorded' | 'unsupported'; summary: string; blockers: string[]}>;
  targets: Array<{id: AutomationTarget; label: string; status: 'ready' | 'blocked'; reason: string}>;
  generation_allowed: boolean; can_generate: boolean; apply_ready: false; automation_gaps: string[]; latest_run: AutomationRun | null;
}
export interface AutomationOutput {report: AutomationRun; files: Array<{path: string; content: string}>}

/** Run the existing Python package pipeline; never execute a user-supplied command. */
export async function projectAutomation<T = ProjectAutomation>(projectId: string, revision: string, run?: {actor: string; targets: AutomationTarget[]}, readRun?: string): Promise<PackageRepositoryResult<T>> {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(projectId) || !/^[a-f0-9]{64}$/.test(revision)) {
    return {available: true, ok: false, status: 422, error: 'Invalid project or revision identifier'};
  }
  const root = process.env.ALUCA_REPO_ROOT || (process.env.NODE_ENV === 'test' ? resolve(process.cwd(), '..') : undefined);
  if (!root) return {available: false, ok: false, status: 503, error: 'Project automation unavailable'};
  const configured = process.env.STUDIO_PACKAGE_DATA_ROOT;
  const dataRoot = configured ? (isAbsolute(configured) ? configured : resolve(process.cwd(), configured)) : join(process.cwd(), 'data', 'project-packages');
  const python = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  const args = [...(!process.env.SUPERVERSION_PYTHON && process.platform === 'win32' ? ['-3'] : []),
    '-m', 'tooling.superversion.project_package.automation', '--repository', join(dataRoot, 'repositories', projectId),
    '--schemas', join(root, 'tooling', 'generator', 'schemas'), '--project-ref', projectId, '--revision', revision];
  if (run) {
    args.push('--run', '--confirm-generation', '--actor', run.actor);
    for (const target of run.targets) args.push('--target', target);
  }
  if (readRun) {
    if (run || !/^[a-f0-9]{64}$/.test(readRun)) return {available: true, ok: false, status: 422, error: 'Invalid run fingerprint'};
    args.push('--read-run',readRun);
  }
  return new Promise(accept => {
    execFile(python, args, {cwd: root, timeout: 60_000, maxBuffer: 32 * 1024 * 1024, env: {...process.env, PYTHONIOENCODING: 'utf-8'}}, (error, stdout) => {
      try {
        const payload = JSON.parse(stdout) as {ok: boolean; value?: T; status?: number; error?: string};
        if (payload.ok && !error && payload.value) accept({available: true, ok: true, value: payload.value});
        else accept({available: true, ok: false, status: payload.status || 409, error: payload.error || 'Automation did not complete'});
      } catch { accept({available: false, ok: false, status: 503, error: 'Automation service did not return a valid result'}); }
    });
  });
}
