import { beforeEach, describe, expect, it, vi } from 'vitest';

type ExecError = Error & { code?: string | number; stdout?: string };
type ExecCallback = (error: ExecError | null, stdout: string, stderr: string) => void;
const { execFileMock } = vi.hoisted(() => ({ execFileMock: vi.fn() }));

vi.mock('node:child_process', () => {
  const shim = (...values: unknown[]) => execFileMock(...values);
  return { default: { execFile: shim }, execFile: shim };
});

import {
  commitProjectPackageDraft,
  diffPackageRevisions,
  getPackageHead,
} from '@/lib/bridge/project-package-repository';

const REVISION = {
  revision_hash: 'a'.repeat(64),
  package_id: 'package_demo',
  project_ref: 'project_demo',
  revision: 1,
  parent_revision_hash: null,
};

function invocation(values: unknown[]): { args: string[]; callback: ExecCallback } {
  const args = values.find(Array.isArray) as string[] | undefined;
  const callback = values.find((value) => typeof value === 'function') as ExecCallback | undefined;
  if (!args || !callback) {
    throw new Error(`Unexpected execFile mock invocation: ${JSON.stringify(values.map((value) => typeof value))}`);
  }
  return { args, callback };
}

beforeEach(() => {
  execFileMock.mockReset();
});

describe('Project Package repository bridge', () => {
  it('returns a verified HEAD and keeps repository paths server-controlled', async () => {
    execFileMock.mockImplementation((...values: unknown[]) => {
      const { args, callback } = invocation(values);
      expect(args).toContain('tooling.superversion.project_package.repository_cli');
      expect(args).toContain('head');
      expect(args.join(' ')).toContain('repositories');
      expect(args.join(' ')).toContain('project_demo');
      callback(null, JSON.stringify({ ok: true, head: REVISION }), '');
    });

    const result = await getPackageHead('project_demo');
    expect(result).toEqual({ available: true, ok: true, value: REVISION });
  });

  it('uses commit-draft so TypeScript does not reimplement revision bookkeeping', async () => {
    execFileMock.mockImplementation((...values: unknown[]) => {
      const { args, callback } = invocation(values);
      expect(args).toContain('commit-draft');
      expect(args).toContain('--expected-head');
      expect(args).toContain('none');
      callback(null, JSON.stringify({ ok: true, revision: REVISION }), '');
    });

    const result = await commitProjectPackageDraft('project_demo', {
      expectedHeadRevisionHash: null,
      files: [{
        path: 'package.yaml',
        sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        size: 0,
        encoding: 'base64',
        contentBase64: '',
      }],
    });
    expect(result.value).toEqual(REVISION);
  });

  it('returns a repository validation failure as available but not successful', async () => {
    execFileMock.mockImplementation((...values: unknown[]) => {
      const { callback } = invocation(values);
      const stdout = JSON.stringify({ ok: false, error: 'invalid project package' });
      callback(Object.assign(new Error('exit 1'), { code: 1, stdout }), stdout, '');
    });

    const result = await diffPackageRevisions('project_demo', 'a'.repeat(64), 'b'.repeat(64));
    expect(result).toEqual({ available: true, ok: false, error: 'invalid project package' });
  });

  it('rejects an unsafe project identifier before spawning Python', async () => {
    const result = await getPackageHead('../outside');
    expect(result).toMatchObject({ available: false, ok: false, error: 'Invalid project identifier' });
    expect(execFileMock).not.toHaveBeenCalled();
  });
});
