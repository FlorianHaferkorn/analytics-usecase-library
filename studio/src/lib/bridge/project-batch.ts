import 'server-only';
import { execFile } from 'node:child_process';
import { isAbsolute, join, resolve } from 'node:path';
import type { PackageRepositoryResult } from './project-package-repository';

export type BatchMode = 'inspect' | 'preview' | 'save' | 'test' | 'export';
/** Fixed local core only. It never reads a source system or calls the tenant runner. */
export function projectBatch<T>(projectId: string, revision: string, mode: BatchMode, input: Record<string, unknown> = {}): Promise<PackageRepositoryResult<T>> {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(projectId) || !/^[a-f0-9]{64}$/.test(revision) || !['inspect', 'preview', 'save', 'test', 'export'].includes(mode)) return Promise.resolve({ available: true, ok: false, status: 422, error: 'Invalid project, version or operation.' });
  const root = process.env.ALUCA_REPO_ROOT || (process.env.NODE_ENV === 'test' ? resolve(process.cwd(), '..') : undefined);
  if (!root) return Promise.resolve({ available: false, ok: false, status: 503, error: 'The trusted Project Package repository is not configured.' });
  const configured = process.env.STUDIO_PACKAGE_DATA_ROOT;
  const dataRoot = configured ? (isAbsolute(configured) ? configured : resolve(process.cwd(), configured)) : join(process.cwd(), 'data', 'project-packages');
  const python = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  const args = [...(!process.env.SUPERVERSION_PYTHON && process.platform === 'win32' ? ['-3'] : []), '-m', 'tooling.superversion.project_package.batch_workbench', '--repository', join(dataRoot, 'repositories', projectId), '--schemas', join(root, 'tooling/generator/schemas'), '--mode', mode];
  return new Promise(accept => {
    const child = execFile(python, args, { cwd: root, windowsHide: true, timeout: 90_000, maxBuffer: 16 * 1024 * 1024, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }, (error, stdout) => {
      try {
        const response = JSON.parse(stdout) as { ok: boolean; value?: T; status?: number; error?: string };
        if (!error && response.ok && response.value) accept({ available: true, ok: true, value: response.value });
        else accept({ available: true, ok: false, status: response.status ?? 409, error: response.error ?? 'The operation was not confirmed. Reload the project version before retrying a save.' });
      } catch { accept({ available: false, ok: false, status: 503, error: 'The local batch engine returned no valid result. Reload the project version before retrying a save.' }); }
    });
    child.stdin?.on('error', () => { /* Completion callback reports failed startup. */ });
    child.stdin?.end(JSON.stringify({ ...input, project_ref: projectId, revision_hash: revision }));
  });
}
