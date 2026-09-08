/** Python remains the sole authority for project architecture derivation and release gates. */
import 'server-only';
import { execFile } from 'node:child_process';
import { isAbsolute, join, resolve } from 'node:path';
import type { PackageRepositoryResult } from './project-package-repository';

export interface ArchitectureNode {
  id: string; label: string; kind: string; layer?: string;
  domain_ref?: string; use_case_ref?: string; details: Record<string, unknown>;
}
export interface ProjectArchitecture {
  schema_version: string; project_ref: string; revision_hash: string; compiler_input_sha256: string;
  architecture: Record<string, unknown> | null; use_cases: Array<Record<string, unknown>>;
  graph: { nodes: ArchitectureNode[]; edges: Array<{ id: string; source: string; target: string; kind: string; label: string }> };
  readiness: { review_ready: boolean; release_ready: boolean; apply_ready: false; blockers: string[] };
  outputs: Array<{ id: ArchitectureTarget; label: string; status: 'ready' | 'blocked'; reason: string }>;
  provenance: Record<string, unknown>;
}
export type ArchitectureTarget = 'architecture_bundle' | 'fabric_workspace_requests';
export interface ProjectArchitectureOutput {
  output_type: ArchitectureTarget;
  manifest: { project_ref: string; revision_hash: string; target: ArchitectureTarget; apply_ready: false; files: Array<{ path: string; sha256: string }> };
  files: Array<{ path: string; content: string }>; limitations: string[];
}

export async function projectArchitecture<T = ProjectArchitecture>(projectId: string, revision?: string, target?: ArchitectureTarget): Promise<PackageRepositoryResult<T>> {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(projectId) || (revision && !/^[a-f0-9]{64}$/.test(revision))) {
    return { available: true, ok: false, status: 422, error: 'Invalid project or revision identifier' };
  }
  const repoRoot = process.env.ALUCA_REPO_ROOT || (process.env.NODE_ENV === 'test' ? resolve(process.cwd(), '..') : undefined);
  if (!repoRoot) return { available: false, ok: false, status: 503, error: 'Project architecture compiler unavailable' };
  const configured = process.env.STUDIO_PACKAGE_DATA_ROOT;
  const dataRoot = configured ? (isAbsolute(configured) ? configured : resolve(process.cwd(), configured)) : join(process.cwd(), 'data', 'project-packages');
  const python = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  const args = [...(!process.env.SUPERVERSION_PYTHON && process.platform === 'win32' ? ['-3'] : []),
    '-m', 'tooling.superversion.project_package.architecture_compile', '--repository', join(dataRoot, 'repositories', projectId),
    '--schemas', join(repoRoot, 'tooling', 'generator', 'schemas'), '--project-ref', projectId];
  if (revision) args.push('--revision', revision);
  if (target) args.push('--target', target);
  return new Promise((accept) => {
    execFile(python, args, { cwd: repoRoot, timeout: 60_000, maxBuffer: 32 * 1024 * 1024, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }, (error, stdout) => {
      try {
        const payload = JSON.parse(stdout) as { ok: boolean; value?: T; error?: string; status?: number };
        if (payload.ok && !error && payload.value) accept({ available: true, ok: true, value: payload.value });
        else accept({ available: true, ok: false, status: payload.status || 409, error: payload.error || 'Architecture generation failed' });
      } catch {
        accept({ available: !error || !('code' in error) || error.code !== 'ENOENT', ok: false, status: 503, error: 'Architecture compiler did not return a valid result' });
      }
    });
  });
}
