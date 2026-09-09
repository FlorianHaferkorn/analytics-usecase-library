import 'server-only';
import { execFile } from 'node:child_process';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { createHash } from 'node:crypto';

export type ReferenceVariant = 'dev_test_prod' | 'dev_prod';
export type EvidenceKind = 'local_check' | 'simulation' | 'tenant_verified' | 'not_verified';
export interface ReferenceCheck { id: string; title: string; status: string; evidence_kind: EvidenceKind; detail: string }
export interface LocalReferenceReport {
  schema_version: string; reference_id: string; run_id: string; variant: ReferenceVariant;
  project_ref: 'local_reference'; revision_hash: string; source_kind: 'synthetic';
  evidence_kind: 'local_check'; tenant_actions_performed: false; live_apply_allowed: false;
  stages: Array<{ id: string; title: string; status: string; evidence_kind: EvidenceKind; summary: string }>;
  checks: ReferenceCheck[];
  graph: { nodes: Array<{ id: string; label: string; kind: string; layer?: string; details: Record<string, unknown> }>;
    edges: Array<{ id: string; source: string; target: string; label: string; kind: string }> };
  files: Array<{ path: string; content: string; sha256: string }>;
  limitations: string[];
}

export function validateLocalReference(value: LocalReferenceReport, variant: ReferenceVariant): LocalReferenceReport {
  if (!value || value.source_kind !== 'synthetic' || value.project_ref !== 'local_reference' || value.variant !== variant
    || value.live_apply_allowed !== false || value.tenant_actions_performed !== false || value.evidence_kind !== 'local_check'
    || !/^[a-f0-9]{64}$/.test(value.revision_hash) || !/^[a-f0-9]{64}$/.test(value.run_id)
    || !Array.isArray(value.stages) || !Array.isArray(value.checks) || !Array.isArray(value.files)
    || !Array.isArray(value.graph?.nodes) || !Array.isArray(value.graph?.edges) || !Array.isArray(value.limitations)) throw new Error('Local reference provenance is invalid. No result is verified.');
  if ([...value.stages, ...value.checks].some(row => !['local_check', 'simulation', 'not_verified'].includes(row.evidence_kind))) throw new Error('A local reference cannot claim tenant verification.');
  const paths = new Set<string>();
  if (!value.files.length || value.files.length > 500) throw new Error('Local reference output inventory is invalid.');
  for (const file of value.files) {
    if (typeof file.path !== 'string' || !file.path || file.path.includes('\\') || file.path.includes(':') || file.path.split('/').some(part => !part || part === '.' || part === '..')
      || paths.has(file.path.toLowerCase()) || typeof file.content !== 'string'
      || createHash('sha256').update(file.content, 'utf8').digest('hex') !== file.sha256) throw new Error('Local reference output integrity check failed.');
    paths.add(file.path.toLowerCase());
  }
  return value;
}

/** Fixed neutral fixture only. No selected-project path, host policy or actor input. */
export async function runLocalReference(variant: ReferenceVariant): Promise<LocalReferenceReport> {
  if (!['dev_test_prod', 'dev_prod'].includes(variant)) throw new Error('Unsupported local reference variant.');
  const repository = process.env.ALUCA_REPO_ROOT || resolve(process.cwd(), '..');
  const scratch = await mkdtemp(join(tmpdir(), 'studio-local-reference-'));
  const python = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  const args = [...(!process.env.SUPERVERSION_PYTHON && process.platform === 'win32' ? ['-3'] : []),
    '-m', 'tooling.superversion.project_package.local_reference', '--root', scratch,
    '--schemas', join(repository, 'tooling/generator/schemas'), '--variant', variant];
  try {
    const value = await new Promise<LocalReferenceReport>((accept, reject) => {
      execFile(python, args, { cwd: repository, windowsHide: true, timeout: 180_000, maxBuffer: 24 * 1024 * 1024,
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }, (error, stdout) => {
        try {
          const response = JSON.parse(stdout) as { ok: boolean; value: LocalReferenceReport };
          if (error || !response.ok) throw new Error('Local reference failed. No tenant operation was requested.');
          accept(validateLocalReference(response.value, variant));
        } catch { reject(new Error('Local reference did not produce a valid, integrity-checked result. Check the local runtime and fixture tests.')); }
      });
    });
    return value;
  } finally {
    // Only the fresh directory created by this invocation is eligible for cleanup.
    if (dirname(scratch) === resolve(tmpdir()) && scratch.startsWith(join(resolve(tmpdir()), 'studio-local-reference-'))) {
      await rm(scratch, { recursive: true, force: true }).catch(() => { /* A timed-out local process may still hold files; never broaden cleanup. */ });
    }
  }
}
