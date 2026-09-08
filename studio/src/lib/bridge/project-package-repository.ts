/**
 * Server-only bridge to the Python-owned Project Package revision repository.
 *
 * TypeScript transports commands and results. It never reimplements package
 * validation, revision sequencing, hashing, diffing or archive verification.
 */

import 'server-only';

import { execFile } from 'node:child_process';
import { isAbsolute, join, resolve } from 'node:path';
import { readFile, writeFile } from 'node:fs/promises';
import {
  readPackageFiles,
  withTemporaryDirectory,
  writePackageFiles,
  type PackageFile,
} from '@/lib/project-package/package-files';

const REPO_ROOT_ENV = ['ALUCA', 'REPO', 'ROOT'].join('_');
const DATA_ROOT_ENV = ['STUDIO', 'PACKAGE', 'DATA', 'ROOT'].join('_');
const REPO_ROOT = process.env[REPO_ROOT_ENV]
  || (process.env.NODE_ENV === 'test' ? resolve(process.cwd(), '..') : undefined);
const configuredDataRoot = process.env[DATA_ROOT_ENV];
const DATA_ROOT = configuredDataRoot
  ? (isAbsolute(configuredDataRoot) ? configuredDataRoot : resolve(process.cwd(), configuredDataRoot))
  : join(process.cwd(), 'data', 'project-packages');
const PYTHON = process.env.SUPERVERSION_PYTHON
  || (process.platform === 'win32' ? 'py' : 'python3');
const PYTHON_ARGS = process.env.SUPERVERSION_PYTHON
  ? []
  : process.platform === 'win32'
    ? ['-3']
    : [];
const PROJECT_ID = /^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/;
const MAX_ARCHIVE_BYTES = 100 * 1024 * 1024;
const MAX_PACKAGE_FILES = 2_000;
const MAX_PACKAGE_FILE_BYTES = 20 * 1024 * 1024;
const MAX_PACKAGE_BYTES = 100 * 1024 * 1024;
const MAX_COMPRESSION_RATIO = 200;

type ExecError = Error & { code?: string | number; stdout?: string };

export interface PackageRevisionSummary {
  revision_hash: string;
  package_id: string;
  project_ref: string;
  revision: number;
  parent_revision_hash: string | null;
}

export interface PackageStructuralDiff {
  from_revision_hash: string;
  to_revision_hash: string;
  added_files: string[];
  removed_files: string[];
  changed_files: Array<Record<string, unknown>>;
}

export interface PackageSnapshot {
  revision: PackageRevisionSummary;
  files: PackageFile[];
}

export interface PackageRepositoryResult<T> {
  available: boolean;
  ok: boolean;
  value?: T;
  error?: string;
  status?: number;
  code?: string;
}

interface CliPayload {
  ok: boolean;
  error?: string;
  status?: number;
  code?: string;
  head?: PackageRevisionSummary | null;
  revision?: PackageRevisionSummary;
  diff?: PackageStructuralDiff;
  output?: string;
  release_bundle?: ProjectReleaseBundle;
}

export interface ProjectReleaseBundle {
  output_type: 'approved_project_input_bundle';
  release: { project_ref: string; revision_hash: string; compiler_input_sha256: string;
    attested_by: string; attested_at: string; rationale: string; record_sha256: string };
  compiler_input: Record<string, unknown>;
  files: PackageFile[];
  limitations: string[];
}

export async function exportApprovedProjectInput(projectId: string, revisionHash: string, attestation?: { actor: string; rationale: string }): Promise<PackageRepositoryResult<ProjectReleaseBundle>> {
  return withTemporaryDirectory('aluca-package-release-', async (temporaryRoot) => {
    const output = join(temporaryRoot, 'approved-input.json');
    const command = ['release-input', '--project-ref', projectId, '--revision', revisionHash, '--output', output];
    if (attestation) command.push('--actor', attestation.actor, '--rationale', attestation.rationale);
    const result = await invoke(projectId, command, (payload) => {
      if (payload.output !== output) throw new Error('Repository returned no approved input bundle');
      return payload.output;
    });
    if (!result.ok) return { ...result, value: undefined };
    return { available: true, ok: true, value: JSON.parse(await readFile(output, 'utf-8')) as ProjectReleaseBundle };
  });
}

function repositoryRoot(projectId: string): string {
  if (!PROJECT_ID.test(projectId)) {
    throw new Error('Invalid project identifier');
  }
  return join(DATA_ROOT, 'repositories', projectId);
}

function spawnRepository(projectId: string, command: string[]): Promise<string> {
  if (!REPO_ROOT) {
    return Promise.reject(Object.assign(
      new Error('Project Package repository unavailable (ALUCA_REPO_ROOT not configured)'),
      { code: 'ECONFIG' },
    ));
  }
  const args = [
    ...PYTHON_ARGS,
    '-m', 'tooling.superversion.project_package.repository_cli',
    '--repository', repositoryRoot(projectId),
    '--schemas', join(REPO_ROOT, 'tooling', 'generator', 'schemas'),
    ...command,
  ];
  return new Promise((resolvePromise, reject) => {
    execFile(
      PYTHON,
      args,
      { cwd: REPO_ROOT, timeout: 60_000, maxBuffer: 16 * 1024 * 1024 },
      (error, stdout) => {
        if (error) {
          (error as ExecError).stdout = stdout;
          reject(error);
        } else {
          resolvePromise(stdout);
        }
      },
    );
  });
}

async function invoke<T>(
  projectId: string,
  command: string[],
  select: (payload: CliPayload) => T,
): Promise<PackageRepositoryResult<T>> {
  try {
    const payload = JSON.parse(await spawnRepository(projectId, command)) as CliPayload;
    if (!payload.ok) {
      return {
        available: true,
        ok: false,
        error: payload.error,
        status: payload.status,
        code: payload.code,
      };
    }
    try {
      return { available: true, ok: true, value: select(payload) };
    } catch (error) {
      return {
        available: true,
        ok: false,
        error: error instanceof Error ? error.message : 'Invalid repository response',
      };
    }
  } catch (cause) {
    const error = cause as ExecError;
    if (error.stdout) {
      try {
        const payload = JSON.parse(error.stdout) as CliPayload;
        return {
          available: true,
          ok: false,
          error: payload.error || error.message,
          status: payload.status,
          code: payload.code,
        };
      } catch {
        // Non-protocol stdout is a transport failure, handled below.
      }
    }
    return {
      available: false,
      ok: false,
      error: error.code === 'ENOENT' ? `${PYTHON} not found` : error.message,
    };
  }
}

export function getPackageHead(projectId: string) {
  return invoke(projectId, ['head'], (payload) => payload.head ?? null);
}

export async function transferDiscoveryToPackage(projectId: string, payload: Record<string, unknown>): Promise<PackageRepositoryResult<PackageRevisionSummary>> {
  return withTemporaryDirectory('aluca-discovery-transfer-', async (temporaryRoot) => {
    const input = join(temporaryRoot, 'review.json');
    await writeFile(input, JSON.stringify({ ...payload, projectId }), 'utf-8');
    return invoke(projectId, ['transfer-discovery', '--input', input], (response) => {
      if (!response.revision || response.revision.project_ref !== projectId) throw new Error('Unexpected Discovery transfer revision');
      return response.revision;
    });
  });
}

export async function loadProjectPackage(
  projectId: string,
  revisionHash?: string,
): Promise<PackageRepositoryResult<PackageSnapshot>> {
  return withTemporaryDirectory('aluca-package-load-', async (temporaryRoot) => {
    const packageRoot = join(temporaryRoot, 'package');
    const command = ['checkout', '--output', packageRoot];
    if (revisionHash) command.push('--revision', revisionHash);
    const checkout = await invoke(projectId, command, (payload) => {
      if (!payload.revision) throw new Error('Repository returned no revision');
      return payload.revision;
    });
    if (!checkout.ok || !checkout.value) {
      return {
        available: checkout.available,
        ok: false,
        error: checkout.error,
        status: checkout.status,
        code: checkout.code,
      };
    }
    try {
      return {
        available: true,
        ok: true,
        value: {
          revision: checkout.value,
          files: await readPackageFiles(packageRoot),
        },
      };
    } catch (error) {
      return {
        available: true,
        ok: false,
        error: error instanceof Error ? error.message : 'Cannot read package snapshot',
      };
    }
  });
}

export async function commitProjectPackageDraft(
  projectId: string,
  draft: { expectedHeadRevisionHash: string | null; files: PackageFile[] },
): Promise<PackageRepositoryResult<PackageRevisionSummary>> {
  return withTemporaryDirectory('aluca-package-save-', async (temporaryRoot) => {
    const packageRoot = join(temporaryRoot, 'package');
    try {
      await writePackageFiles(packageRoot, draft.files);
    } catch (error) {
      return {
        available: true,
        ok: false,
        error: error instanceof Error ? error.message : 'Invalid package file map',
      };
    }
    return invoke(
      projectId,
      [
        'commit-draft',
        '--package', packageRoot,
        '--expected-head', draft.expectedHeadRevisionHash ?? 'none',
      ],
      (payload) => {
        if (!payload.revision) throw new Error('Repository returned no revision');
        return payload.revision;
      },
    );
  });
}

export function diffPackageRevisions(projectId: string, fromRevision: string, toRevision: string) {
  return invoke(
    projectId,
    ['diff', '--from-revision', fromRevision, '--to-revision', toRevision],
    (payload) => {
      if (!payload.diff) throw new Error('Repository returned no diff');
      return payload.diff;
    },
  );
}

export async function exportProjectPackageHistory(
  projectId: string,
): Promise<PackageRepositoryResult<{ archive: Uint8Array; head: PackageRevisionSummary }>> {
  return withTemporaryDirectory('aluca-package-export-', async (temporaryRoot) => {
    const outputZip = join(temporaryRoot, 'project-package-history.zip');
    const exported = await invoke(projectId, ['export', '--output', outputZip], (payload) => {
      if (!payload.head) throw new Error('Repository returned no HEAD');
      return payload.head;
    });
    if (!exported.ok || !exported.value) {
      return {
        available: exported.available,
        ok: false,
        error: exported.error,
        status: exported.status,
        code: exported.code,
      };
    }
    const archive = await readFile(outputZip);
    return {
      available: true,
      ok: true,
      value: { archive, head: exported.value },
    };
  });
}

export async function importProjectPackageHistory(
  projectId: string,
  archive: Uint8Array,
): Promise<PackageRepositoryResult<PackageRevisionSummary>> {
  if (archive.byteLength === 0 || archive.byteLength > MAX_ARCHIVE_BYTES) {
    return { available: true, ok: false, error: 'Package history archive size is outside the allowed range' };
  }
  return withTemporaryDirectory('aluca-package-import-', async (temporaryRoot) => {
    const inputZip = join(temporaryRoot, 'project-package-history.zip');
    await writeFile(inputZip, archive);
    return invoke(projectId, [
      'import',
      '--input', inputZip,
      '--max-members', String(MAX_PACKAGE_FILES),
      '--max-member-bytes', String(MAX_PACKAGE_FILE_BYTES),
      '--max-total-bytes', String(MAX_PACKAGE_BYTES),
      '--max-compression-ratio', String(MAX_COMPRESSION_RATIO),
    ], (payload) => {
      if (!payload.head) throw new Error('Repository returned no HEAD');
      return payload.head;
    });
  });
}
