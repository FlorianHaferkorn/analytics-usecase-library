import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('@/lib/core/bracket-loader', () => ({
  resolveBracketPath: vi.fn(),
}));

type ExecCb = (err: (Error & { code?: string | number; stdout?: string }) | null, stdout: string, stderr: string) => void;
const { execFileMock } = vi.hoisted(() => ({ execFileMock: vi.fn() }));
vi.mock('node:child_process', () => {
  const shim = (_cmd: string, _args: string[], _opts: unknown, cb: ExecCb) => execFileMock(_args, cb);
  return { default: { execFile: shim }, execFile: shim };
});

import { runGenerate } from '@/lib/bridge/superversion-bridge';
import { resolveBracketPath } from '@/lib/core/bracket-loader';

const GREEN = {
  ok: true,
  bracket: 'COM-001_Sales_Performance',
  target: 'tmdl',
  target_label: 'TMDL semantic model',
  target_status: 'live',
  targets_available: ['pbir', 'tmdl'],
  artifacts: [{ path: 'COM-001.SemanticModel/measures.tmdl', bytes: 512 }],
  gate: { ok: true, stages: [{ name: 'source', status: 'PASS', detail: 'ok' }] },
};

beforeEach(() => {
  vi.mocked(resolveBracketPath).mockReset();
  execFileMock.mockReset();
});

describe('runGenerate', () => {
  it('maps the bridge payload (snake → camel) on a green gate', async () => {
    vi.mocked(resolveBracketPath).mockResolvedValue('/repo/.../UseCase_Bracket.yaml');
    execFileMock.mockImplementation((_args: string[], cb: ExecCb) => cb(null, JSON.stringify(GREEN), ''));

    const result = await runGenerate('COM-001', 'tmdl');
    expect(result).toMatchObject({ available: true, ok: true, target: 'tmdl', targetLabel: 'TMDL semantic model', targetStatus: 'live' });
    expect(result.targetsAvailable).toEqual(['pbir', 'tmdl']);
    expect(result.artifacts[0].bytes).toBe(512);
    expect(result.gate?.ok).toBe(true);
  });

  it('reports a red gate as available but not ok', async () => {
    const RED = { ...GREEN, ok: false, gate: { ok: false, stages: [{ name: 'pbir', status: 'FAIL', detail: '2 errors' }] } };
    vi.mocked(resolveBracketPath).mockResolvedValue('/repo/.../UseCase_Bracket.yaml');
    execFileMock.mockImplementation((_args: string[], cb: ExecCb) => cb(null, JSON.stringify(RED), ''));

    const result = await runGenerate('COM-001');
    expect(result.available).toBe(true);
    expect(result.ok).toBe(false);
    expect(result.gate?.stages[0].status).toBe('FAIL');
  });

  it('surfaces an unknown-target JSON error from a non-zero exit', async () => {
    vi.mocked(resolveBracketPath).mockResolvedValue('/repo/.../UseCase_Bracket.yaml');
    execFileMock.mockImplementation((_args: string[], cb: ExecCb) => {
      const err = Object.assign(new Error('exit 1'), { code: 1, stdout: JSON.stringify({ ok: false, error: "unknown target 'nope'" }) });
      cb(err, err.stdout, '');
    });
    const result = await runGenerate('COM-001', 'nope');
    expect(result).toMatchObject({ available: true, ok: false });
    expect(result.error).toContain('unknown target');
  });

  it('degrades honestly when the bridge cannot run (ENOENT)', async () => {
    vi.mocked(resolveBracketPath).mockResolvedValue('/repo/.../UseCase_Bracket.yaml');
    execFileMock.mockImplementation((_args: string[], cb: ExecCb) => cb(Object.assign(new Error('spawn ENOENT'), { code: 'ENOENT' }), '', ''));
    const result = await runGenerate('COM-001');
    expect(result.available).toBe(false);
    expect(result.error).toMatch(/unavailable/);
  });
});
