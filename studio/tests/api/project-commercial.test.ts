import { beforeEach, describe, expect, it, vi } from 'vitest';
const mocks = vi.hoisted(() => ({ role: vi.fn(), engine: vi.fn() }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: mocks.role }));
vi.mock('@/lib/bridge/project-commercial', async () => {
  const actual = await vi.importActual<typeof import('@/lib/bridge/project-commercial')>('@/lib/bridge/project-commercial');
  return { ...actual, projectCommercialImpact: mocks.engine };
});
const hash = 'a'.repeat(64);
const context = { params: Promise.resolve({ projectId: 'alpha' }) };
const url = (query: string) => new Request(`http://x/commercial?${query}`);
const valid = `revision=${hash}&decision=decision_environment_model&option=dev_prod`;
const result = () => ({ project_ref: 'alpha', baseline_revision_hash: hash, decision_ref: 'decision_environment_model', alternative_option_ref: 'dev_prod',
  status: 'evaluated', price_values_embedded: false, baseline: { hours_by_canon_role: { tester: 9 } }, alternative: { hours_by_canon_role: { tester: 6 } } });
beforeEach(() => {
  vi.clearAllMocks();
  mocks.role.mockResolvedValue([{ email: 'editor@example.test' }, null]);
  mocks.engine.mockResolvedValue({ ok: true, value: result() });
});
describe('Commercial comparison API', () => {
  it('requires the editor role before evaluating', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/commercial/route');
    mocks.role.mockResolvedValue([null, new Response('denied', { status: 403 })]);
    expect((await GET(url(valid), context)).status).toBe(403);
    expect(mocks.role).toHaveBeenCalledWith('editor', 'alpha');
    expect(mocks.engine).not.toHaveBeenCalled();
  });
  it('requires pinned identifiers and prevents caching', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/commercial/route');
    for (const query of ['', `revision=HEAD&decision=d&option=o`, `revision=${hash}&decision=D&option=dev_prod`]) {
      expect((await GET(url(query), context)).status).toBe(422);
    }
    const response = await GET(url(valid), context);
    expect(response.status).toBe(200);
    expect(response.headers.get('cache-control')).toBe('private, no-store');
  });
  it('withholds any result that carries a rate or price field', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/commercial/route');
    for (const patch of [{ price_values_embedded: true }, { preis_gerundet: 1 }, { baseline: { packages: [{ kostensatz_eur_h: 90 }] } }, { alternative: { price_band: [1, 2] } }]) {
      mocks.engine.mockResolvedValueOnce({ ok: true, value: { ...result(), ...patch } });
      const response = await GET(url(valid), context);
      expect(response.status).toBe(409);
      expect(JSON.stringify(await response.json())).not.toMatch(/90|price_band/);
    }
  });
  it('rejects a mismatched identity', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/commercial/route');
    mocks.engine.mockResolvedValueOnce({ ok: true, value: { ...result(), project_ref: 'beta' } });
    expect((await GET(url(valid), context)).status).toBe(409);
  });
});
