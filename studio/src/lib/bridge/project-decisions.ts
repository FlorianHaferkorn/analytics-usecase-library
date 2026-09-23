import 'server-only';

import { execFile } from 'node:child_process';
import { isAbsolute, join, resolve } from 'node:path';
import type { PackageRepositoryResult } from './project-package-repository';

export interface DecisionTarget {
  collection: string;
  entity_id: string | null;
  field: string;
}

export interface DecisionPreview {
  project_ref: string;
  revision_hash: string;
  preview_sha256: string;
  can_apply: boolean;
  changes: Array<{
    rule_id: string;
    decision_ref: string;
    target: DecisionTarget;
    before: unknown;
    after: unknown;
    rationale: string;
  }>;
  blockers: string[];
  rules: Array<{ id: string; status: string; reason: string }>;
}

export interface DecisionApplication {
  project_ref: string;
  revision_hash: string;
  parent_revision_hash: string;
  audit_ref: string;
  state: 'working';
  release_required: true;
}

/** Python owns rule evaluation, approval checks, hashes and immutable mutation. */
export function projectDecisions<T>(
  projectId: string,
  revision: string,
  review?: { previewHash: string; actor: string; rationale: string },
): Promise<PackageRepositoryResult<T>> {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(projectId) || !/^[a-f0-9]{64}$/.test(revision)) {
    return Promise.resolve({ available: true, ok: false, status: 422, error: 'Invalid project or revision' });
  }
  const root = process.env.ALUCA_REPO_ROOT || (process.env.NODE_ENV === 'test' ? resolve(process.cwd(), '..') : undefined);
  if (!root) return Promise.resolve({ available: false, ok: false, status: 503, error: 'Decision derivation is not configured' });
  const configured = process.env.STUDIO_PACKAGE_DATA_ROOT;
  const dataRoot = configured ? (isAbsolute(configured) ? configured : resolve(process.cwd(), configured)) : join(process.cwd(), 'data', 'project-packages');
  const python = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  const args = [
    ...(!process.env.SUPERVERSION_PYTHON && process.platform === 'win32' ? ['-3'] : []),
    '-m', 'tooling.superversion.project_package.decision_derivation',
    '--repository', join(dataRoot, 'repositories', projectId),
    '--schemas', join(root, 'tooling', 'generator', 'schemas'),
    '--mode', review ? 'apply' : 'preview',
  ];
  const input = { project_ref: projectId, revision_hash: revision, ...(review ? {
    preview_sha256: review.previewHash, actor: review.actor, rationale: review.rationale, confirm_apply: true,
  } : {}) };
  return new Promise(accept => {
    const child = execFile(python, args, { cwd: root, timeout: 60_000, maxBuffer: 8 * 1024 * 1024, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }, (error, stdout) => {
      try {
        const result = JSON.parse(stdout) as { ok: boolean; value?: T; error?: string; status?: number };
        if (!error && result.ok && result.value) accept({ available: true, ok: true, value: result.value });
        else accept({ available: true, ok: false, status: result.status || 409, error: result.error || 'Outcome could not be confirmed. Reload Package HEAD before retrying.' });
      } catch {
        accept({ available: false, ok: false, status: 503, error: review ? 'Update outcome could not be confirmed. Reload Package HEAD before retrying.' : 'Decision engine did not return a valid result' });
      }
    });
    child.stdin?.on('error', () => { /* The process callback handles failed startup. */ });
    child.stdin?.end(JSON.stringify(input));
  });
}
