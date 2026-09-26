import { beforeEach, describe, expect, it, vi } from 'vitest';
const mocks = vi.hoisted(() => ({ role: vi.fn(), engine: vi.fn() }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: mocks.role }));
vi.mock('@/lib/bridge/project-alternatives', () => ({ projectAlternativeImpact: mocks.engine }));
const hash = 'a'.repeat(64);
const context = { params: Promise.resolve({ projectId: 'alpha' }) };
const url = (query: string) => new Request(`http://x/alternatives?${query}`);
const valid = `revision=${hash}&decision=decision_environment_model&option=dev_prod`;
const impact = () => ({ project_ref: 'alpha', baseline_revision_hash: hash, decision_ref: 'decision_environment_model', alternative_option_ref: 'dev_prod',
  baseline_unchanged: true, approval_granted: false, release_granted: false, tenant_actions_performed: false });
beforeEach(() => {
  vi.clearAllMocks();
  mocks.role.mockResolvedValue([{ email: 'viewer@example.test' }, null]);
  mocks.engine.mockResolvedValue({ ok: true, value: impact() });
});
describe('Alternative comparison API', () => {
  it('authorizes the project before comparing', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/alternatives/route');
    mocks.role.mockResolvedValue([null, new Response('denied', { status: 403 })]);
    expect((await GET(url(valid), context)).status).toBe(403);
    expect(mocks.engine).not.toHaveBeenCalled();
  });
  it('requires a pinned revision, decision and option and prevents caching', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/alternatives/route');
    for (const query of ['', `revision=${hash}`, `revision=HEAD&decision=d&option=o`, `revision=${hash}&decision=D-1&option=dev_prod`, `revision=${hash}&decision=d&option=../x`]) {
      expect((await GET(url(query), context)).status).toBe(422);
    }
    expect(mocks.engine).not.toHaveBeenCalled();
    const response = await GET(url(valid), context);
    expect(response.status).toBe(200);
    expect(response.headers.get('cache-control')).toBe('private, no-store');
    expect(mocks.role).toHaveBeenCalledWith('viewer', 'alpha');
    expect(mocks.engine).toHaveBeenCalledWith('alpha', hash, 'decision_environment_model', 'dev_prod');
  });
  it('rejects a foreign or mismatched result', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/alternatives/route');
    for (const patch of [{ project_ref: 'beta' }, { baseline_revision_hash: 'b'.repeat(64) }, { alternative_option_ref: 'dev_test_prod' }, { decision_ref: 'other' }]) {
      mocks.engine.mockResolvedValueOnce({ ok: true, value: { ...impact(), ...patch } });
      expect((await GET(url(valid), context)).status).toBe(409);
    }
  });
  it('refuses a result that claims approval, release, tenant action or a changed baseline', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/alternatives/route');
    for (const patch of [{ approval_granted: true }, { release_granted: true }, { tenant_actions_performed: true }, { baseline_unchanged: false }]) {
      mocks.engine.mockResolvedValueOnce({ ok: true, value: { ...impact(), ...patch } });
      expect((await GET(url(valid), context)).status).toBe(409);
    }
  });
  it('passes engine refusals through without pretending a comparison exists', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/alternatives/route');
    mocks.engine.mockResolvedValueOnce({ ok: false, status: 409, error: 'Release blocked: this revision has no explicit release attestation' });
    const response = await GET(url(valid), context);
    expect(response.status).toBe(409);
    expect((await response.json()).error).toMatch(/release attestation/);
  });
});
