import { createHash } from 'node:crypto';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { beforeEach, describe, expect, it, vi } from 'vitest';
const fake = vi.hoisted(() => ({ exec: vi.fn(), mkdir: vi.fn(), rm: vi.fn() }));
vi.mock('node:child_process', () => ({ execFile: fake.exec, default: { execFile: fake.exec } }));
vi.mock('node:fs/promises', () => ({ mkdtemp: fake.mkdir, rm: fake.rm, default: { mkdtemp: fake.mkdir, rm: fake.rm } }));
import { runLocalReference, validateLocalReference, type LocalReferenceReport } from '@/lib/bridge/local-reference';
function report(): LocalReferenceReport {
  return { schema_version: '1.0.0', reference_id: 'synthetic', run_id: 'a'.repeat(64), variant: 'dev_test_prod', project_ref: 'local_reference', revision_hash: 'b'.repeat(64), source_kind: 'synthetic', evidence_kind: 'local_check', tenant_actions_performed: false, live_apply_allowed: false,
    stages: [{ id: 'input', title: 'Input', status: 'passed', evidence_kind: 'local_check', summary: 'Synthetic' }], checks: [], graph: { nodes: [], edges: [] }, limitations: ['No tenant'],
    files: [{ path: 'docs/reference.md', content: 'Synthetic → output', sha256: createHash('sha256').update('Synthetic → output').digest('hex') }] };
}
beforeEach(() => {
  vi.clearAllMocks(); fake.mkdir.mockResolvedValue(join(tmpdir(), 'studio-local-reference-test')); fake.rm.mockResolvedValue(undefined);
  fake.exec.mockImplementation((_python, _args, _options, callback) => callback(null, JSON.stringify({ ok: true, value: report() })));
});
describe('Local reference provenance and transport', () => {
  it('accepts a UTF-8 integrity-checked synthetic report', () => expect(validateLocalReference(report(), 'dev_test_prod')).toEqual(report()));
  it.each(['source_kind', 'project_ref', 'variant', 'revision_hash', 'run_id', 'live_apply_allowed', 'tenant_actions_performed', 'evidence_kind'])('rejects a changed provenance field %s', field => {
    const value = { ...report(), [field]: 'changed' } as LocalReferenceReport;
    expect(() => validateLocalReference(value, 'dev_test_prod')).toThrow();
  });
  it.each(['../escape', '/absolute', 'C:/drive', 'a\\b', 'a//b', './file', 'a/../b'])('rejects unsafe output path %s', path => {
    const value = report(); value.files[0].path = path; expect(() => validateLocalReference(value, 'dev_test_prod')).toThrow();
  });
  it('rejects a forged hash, duplicate Windows path, or tenant evidence', () => {
    const hash = report(); hash.files[0].content += 'changed'; expect(() => validateLocalReference(hash, 'dev_test_prod')).toThrow();
    const duplicate = report(); duplicate.files.push({ ...duplicate.files[0], path: duplicate.files[0].path.toUpperCase() }); expect(() => validateLocalReference(duplicate, 'dev_test_prod')).toThrow();
    const forged = report(); forged.stages[0].evidence_kind = 'tenant_verified'; expect(() => validateLocalReference(forged, 'dev_test_prod')).toThrow();
  });
  it('runs only a fixed module and removes only its newly created directory', async () => {
    expect(await runLocalReference('dev_test_prod')).toEqual(report());
    const [, args, options] = fake.exec.mock.calls[0];
    expect(args).toContain('tooling.superversion.project_package.local_reference');
    expect(args.slice(-2)).toEqual(['--variant', 'dev_test_prod']); expect(args).not.toContain('execute');
    expect(options.windowsHide).toBe(true); expect(options.env.PYTHONIOENCODING).toBe('utf-8');
    expect(fake.rm).toHaveBeenCalledWith(join(tmpdir(), 'studio-local-reference-test'), { recursive: true, force: true });
  });
  it('cleans up and sanitizes a failed process', async () => {
    fake.exec.mockImplementation((_p, _a, _o, callback) => callback(new Error('secret'), 'invalid'));
    await expect(runLocalReference('dev_test_prod')).rejects.toThrow('valid, integrity-checked'); expect(fake.rm).toHaveBeenCalledTimes(1);
  });
  it('never broadens cleanup to a different directory or accepts an unknown variant', async () => {
    fake.mkdir.mockResolvedValue(join(tmpdir(), 'unrelated'));
    await runLocalReference('dev_test_prod'); expect(fake.rm).not.toHaveBeenCalled();
    await expect(runLocalReference('unknown' as never)).rejects.toThrow('Unsupported');
  });
});
