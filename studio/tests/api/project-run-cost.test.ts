import { beforeEach, describe, expect, it, vi } from 'vitest';
const mocks = vi.hoisted(() => ({ role: vi.fn(), engine: vi.fn() }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: mocks.role }));
vi.mock('@/lib/bridge/project-run-cost', () => ({ projectRunCostDelta: mocks.engine }));
const hash = 'a'.repeat(64);
const context = { params: Promise.resolve({ projectId: 'alpha' }) };
const url = (query: string) => new Request(`http://x/run-cost?${query}`);
const valid = `revision=${hash}&decision=decision_environment_model&option=dev_prod`;
const result = () => ({ project_ref: 'alpha', baseline_revision_hash: hash, decision_ref: 'decision_environment_model',
  alternative_option_ref: 'dev_prod', status: 'evaluated', persist: false });
beforeEach(() => {
  vi.clearAllMocks();
  mocks.role.mockResolvedValue([{ email: 'viewer@example.test' }, null]);
  mocks.engine.mockResolvedValue({ ok: true, value: result() });
});
describe('Run-cost API', () => {
  it('is open to viewers because it carries list prices only', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/run-cost/route');
    expect((await GET(url(valid), context)).status).toBe(200);
    expect(mocks.role).toHaveBeenCalledWith('viewer', 'alpha');
  });
  it('stops before evaluating when the role is missing', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/run-cost/route');
    mocks.role.mockResolvedValue([null, new Response('denied', { status: 403 })]);
    expect((await GET(url(valid), context)).status).toBe(403);
    expect(mocks.engine).not.toHaveBeenCalled();
  });
  it('requires pinned identifiers and prevents caching', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/run-cost/route');
    for (const query of ['', `revision=HEAD&decision=d&option=o`, `revision=${hash}&decision=D&option=dev_prod`]) {
      expect((await GET(url(query), context)).status).toBe(422);
    }
    expect((await GET(url(valid), context)).headers.get('cache-control')).toBe('private, no-store');
  });
  it('rejects a mismatched identity or a persistable result', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/run-cost/route');
    for (const patch of [{ project_ref: 'beta' }, { persist: true }]) {
      mocks.engine.mockResolvedValueOnce({ ok: true, value: { ...result(), ...patch } });
      expect((await GET(url(valid), context)).status).toBe(409);
    }
  });
});
