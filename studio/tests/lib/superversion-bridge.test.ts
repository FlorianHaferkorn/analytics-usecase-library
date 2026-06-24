import { describe, it, expect, vi, beforeEach } from 'vitest';

// Control the bracket-path resolver and the spawned subprocess.
vi.mock('@/lib/core/bracket-loader', () => ({
  resolveBracketPath: vi.fn(),
}));

type ExecCb = (err: (Error & { code?: string | number; stdout?: string }) | null, stdout: string, stderr: string) => void;
const { execFileMock } = vi.hoisted(() => ({ execFileMock: vi.fn() }));
vi.mock('node:child_process', () => {
  const shim = (_cmd: string, _args: string[], _opts: unknown, cb: ExecCb) => execFileMock(_args, cb);
  return { default: { execFile: shim }, execFile: shim };
});

import { runPreCore } from '@/lib/bridge/superversion-bridge';
import { resolveBracketPath } from '@/lib/core/bracket-loader';

const PAYLOAD = {
  ok: true,
  bracket: 'COM-001_Sales_Performance',
  engines: [
    { id: 'gov', label: 'Governance audit (Beta)', status: 'beta', ok: true, counts: { info: 0, warn: 0, error: 0 }, findings: [] },
  ],
};

beforeEach(() => {
  vi.mocked(resolveBracketPath).mockReset();
  execFileMock.mockReset();
});

describe('runPreCore', () => {
  it('returns the core verdict on a successful bridge run', async () => {
    vi.mocked(resolveBracketPath).mockResolvedValue('/repo/core/usecases/core/COM-001_X/UseCase_Bracket.yaml');
    execFileMock.mockImplementation((_args: string[], cb: ExecCb) => cb(null, JSON.stringify(PAYLOAD), ''));

    const result = await runPreCore('COM-001');
    expect(result).toMatchObject({ available: true, ok: true, bracket: 'COM-001_Sales_Performance' });
    expect(result.engines[0].id).toBe('gov');
  });

  it('flags bracket-not-found as a core verdict (still available)', async () => {
    vi.mocked(resolveBracketPath).mockResolvedValue(null);
    const result = await runPreCore('ZZZ-999');
    expect(result.available).toBe(true);
    expect(result.ok).toBe(false);
    expect(result.error).toContain('ZZZ-999');
    expect(execFileMock).not.toHaveBeenCalled();
  });

  it('surfaces a JSON error carried on stdout of a non-zero exit', async () => {
    vi.mocked(resolveBracketPath).mockResolvedValue('/repo/.../UseCase_Bracket.yaml');
    execFileMock.mockImplementation((_args: string[], cb: ExecCb) => {
      const err = Object.assign(new Error('exit 1'), { code: 1, stdout: JSON.stringify({ ok: false, error: 'bracket not found: x' }) });
      cb(err, err.stdout, '');
    });
    const result = await runPreCore('COM-001');
    expect(result).toMatchObject({ available: true, ok: false, error: 'bracket not found: x' });
  });

  it('degrades honestly when the python interpreter is missing (ENOENT)', async () => {
    vi.mocked(resolveBracketPath).mockResolvedValue('/repo/.../UseCase_Bracket.yaml');
    execFileMock.mockImplementation((_args: string[], cb: ExecCb) => {
      cb(Object.assign(new Error('spawn ENOENT'), { code: 'ENOENT' }), '', '');
    });
    const result = await runPreCore('COM-001');
    expect(result.available).toBe(false);
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/unavailable/);
  });
});
