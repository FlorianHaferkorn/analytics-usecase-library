import 'server-only';
import { execFile } from 'node:child_process';
import { isAbsolute, join, resolve } from 'node:path';
import type { PackageRepositoryResult } from './project-package-repository';

export interface RunnerCheck {
  id: string;
  title: string;
  state: 'configured' | 'missing' | 'not_verified';
  detail: string;
  action: string;
}
export interface RunnerStatus {
  project_ref: string;
  enabled: boolean;
  can_approve: boolean;
  can_execute: boolean;
  identity_broker_available: boolean;
  environments: string[];
  limitations: string[];
  checks?: RunnerCheck[];
  checked_at?: string;
  readiness_scope?: 'configuration_only';
  tenant_actions_performed?: false;
}
export interface RunnerApproval {
  approval_id: string;
  project_ref: string;
  revision_hash: string;
  plan_sha256: string;
  expires_at: string;
  status?: 'approved_not_executed';
}
export interface RunnerResult {
  approval_id: string;
  project_ref: string;
  revision_hash: string;
  plan_sha256: string;
  outcome: { status: string; recovery?: string; whole_project_verified?: boolean; [key: string]: unknown };
}
export interface RunnerEvidence {
  status: 'approved_not_executed' | 'expired' | 'consumed_requires_reconciliation' | 'completed';
  receipt: RunnerApproval;
  result?: RunnerResult;
}

/** Trusted host configuration only. There are no client-selected commands or paths. */
export function projectRunner<T>(projectId: string, revision: string, actor: string,
  action: { mode: 'status' } | { mode: 'approve'; plan: Record<string, unknown>; rationale: string }
    | { mode: 'execute' | 'outcome'; approvalId: string }): Promise<PackageRepositoryResult<T>> {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(projectId) || !/^[a-f0-9]{64}$/.test(revision)) {
    return Promise.resolve({ available: true, ok: false, status: 422, error: 'Invalid project or version' });
  }
  const root = process.env.ALUCA_REPO_ROOT || (process.env.NODE_ENV === 'test' ? resolve(process.cwd(), '..') : undefined);
  if (!root) return Promise.resolve({ available: false, ok: false, status: 503, error: 'Runner host is not configured' });
  const configured = process.env.STUDIO_PACKAGE_DATA_ROOT;
  const dataRoot = configured ? (isAbsolute(configured) ? configured : resolve(process.cwd(), configured)) : join(process.cwd(), 'data', 'project-packages');
  const python = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  const args = [...(!process.env.SUPERVERSION_PYTHON && process.platform === 'win32' ? ['-3'] : []),
    '-m', 'tooling.superversion.project_package.runner_host', '--repository', join(dataRoot, 'repositories', projectId),
    '--schemas', join(root, 'tooling', 'generator', 'schemas'), '--mode', action.mode];
  const input = { project_ref: projectId, revision_hash: revision, actor,
    ...(action.mode === 'approve' ? { plan: action.plan, rationale: action.rationale, confirm: true } : {}),
    ...('approvalId' in action ? { approval_id: action.approvalId } : {}),
    ...(action.mode === 'execute' ? { confirm: true } : {}),
  };
  return new Promise(accept => {
    const child = execFile(python, args, { cwd: root, timeout: action.mode === 'execute' ? 180_000 : 60_000,
      maxBuffer: 8 * 1024 * 1024, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }, (error, stdout) => {
      try {
        const result = JSON.parse(stdout) as { ok: boolean; value?: T; error?: string; status?: number };
        if (!error && result.ok && result.value) accept({ available: true, ok: true, value: result.value });
        else accept({ available: true, ok: false, status: result.status || 409, error: result.error || 'Runner outcome is uncertain. Read the saved evidence before any retry.' });
      } catch {
        accept({ available: false, ok: false, status: 503, error: action.mode === 'execute'
          ? 'Execution outcome is uncertain. Do not execute again. Retrieve the saved outcome and reconcile the tenant.'
          : 'Runner host did not return a valid result. No outcome is confirmed.' });
      }
    });
    child.stdin?.on('error', () => { /* Completion is handled by the child-process callback. */ });
    child.stdin?.end(JSON.stringify(input));
  });
}
