// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
const fake = vi.hoisted(() => ({ exec: vi.fn(), end: vi.fn(), on: vi.fn() }));
vi.mock('node:child_process', () => ({ execFile: fake.exec, default: { execFile: fake.exec } }));
import { projectBatch } from '@/lib/bridge/project-batch';
const hash = 'a'.repeat(64);
beforeEach(() => {
  vi.clearAllMocks();
  fake.exec.mockImplementation((_python, _args, _options, callback) => { callback(null, JSON.stringify({ ok: true, value: { local: true } })); return { stdin: { end: fake.end, on: fake.on } }; });
});
afterEach(() => vi.unstubAllEnvs());
describe('Fixed local batch transport', () => {
  it.each(['alpha', 'project-demo', '1290a7e9-483b-4f23-a8c8-0798eca87e96', 'Project_1'])('preserves valid existing project ID %s', async id => {
    expect((await projectBatch(id, hash, 'inspect')).ok).toBe(true);
    const [, args, options] = fake.exec.mock.calls[0];
    expect(args).toContain('tooling.superversion.project_package.batch_workbench');
    expect(args).not.toContain('execute'); expect(options.windowsHide).toBe(true);
    expect(options.env.PYTHONIOENCODING).toBe('utf-8');
    expect(JSON.parse(fake.end.mock.calls[0][0])).toEqual({ project_ref: id, revision_hash: hash });
  });
  it.each(['../alpha', 'C:/alpha', 'a\\b', '', '-alpha', 'x'.repeat(65)])('rejects invalid identity %s without spawn', async id => {
    expect((await projectBatch(id, hash, 'inspect')).ok).toBe(false); expect(fake.exec).not.toHaveBeenCalled();
  });
  it('pins identities after supplied payload fields and keeps values off command line', async () => {
    await projectBatch('alpha', hash, 'preview', { project_ref: 'other', revision_hash: 'other', contract: { object: 'private-example' } });
    expect(fake.exec.mock.calls[0][1].join(' ')).not.toContain('private-example');
    expect(JSON.parse(fake.end.mock.calls[0][0])).toMatchObject({ project_ref: 'alpha', revision_hash: hash });
  });
  it('sanitizes process errors and missing output', async () => {
    fake.exec.mockImplementation((_p, _a, _o, callback) => { callback(new Error('secret-path'), 'not-json'); return { stdin: { end: fake.end, on: fake.on } }; });
    const result = await projectBatch('alpha', hash, 'test');
    expect(result.status).toBe(503); expect(result.error).not.toContain('secret-path');
  });
  it('does not spawn without operator configuration outside tests', async () => {
    vi.stubEnv('NODE_ENV', 'production'); vi.stubEnv('ALUCA_REPO_ROOT', '');
    expect((await projectBatch('alpha', hash, 'inspect')).status).toBe(503); expect(fake.exec).not.toHaveBeenCalled();
  });
});
