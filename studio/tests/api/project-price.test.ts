import { beforeEach, describe, expect, it, vi } from 'vitest';
const mocks = vi.hoisted(() => ({ role: vi.fn(), engine: vi.fn(), audit: vi.fn() }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: mocks.role }));
vi.mock('@/lib/bridge/project-price', () => ({ projectPriceDelta: mocks.engine }));
vi.mock('@/lib/db/audit-repo', () => ({ logAuditEvent: mocks.audit }));
const hash = 'a'.repeat(64);
const context = { params: Promise.resolve({ projectId: 'alpha' }) };
const url = (query: string) => new Request(`http://x/price?${query}`);
const valid = `revision=${hash}&decision=decision_environment_model&option=dev_prod`;
const totals = { cost: 1000, price_calculated: 1500, price_rounded: 1500, list_price: 1600 };
const result = () => ({ project_ref: 'alpha', baseline_revision_hash: hash, decision_ref: 'decision_environment_model', alternative_option_ref: 'dev_prod',
  status: 'evaluated', price_values_embedded: true, persist: false, currency: 'EUR', tenant_fingerprint_sha256: 'f'.repeat(64),
  baseline: { packages: [], totals, priced_packages: 1, unpriced: [] }, alternative: { packages: [], totals, priced_packages: 1, unpriced: [] },
  delta: { cost: 0, price_calculated: 0, price_rounded: 0, list_price: 0 }, comparable: true });
beforeEach(() => {
  vi.clearAllMocks();
  mocks.role.mockResolvedValue([{ email: 'admin@example.test' }, null]);
  mocks.engine.mockResolvedValue({ ok: true, value: result() });
});
describe('Price delta API', () => {
  it('requires the admin role before evaluating', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/commercial/price/route');
    mocks.role.mockResolvedValue([null, new Response('denied', { status: 403 })]);
    expect((await GET(url(valid), context)).status).toBe(403);
    expect(mocks.role).toHaveBeenCalledWith('admin', 'alpha');
    expect(mocks.engine).not.toHaveBeenCalled();
  });
  it('requires pinned identifiers and never allows caching', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/commercial/price/route');
    for (const query of ['', `revision=HEAD&decision=d&option=o`, `revision=${hash}&decision=D&option=dev_prod`]) {
      expect((await GET(url(query), context)).status).toBe(422);
    }
    const response = await GET(url(valid), context);
    expect(response.status).toBe(200);
    expect(response.headers.get('cache-control')).toBe('private, no-store');
  });
  it('audits the view with hashes only, never an amount', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/commercial/price/route');
    await GET(url(valid), context);
    expect(mocks.audit).toHaveBeenCalledOnce();
    const logged = JSON.stringify(mocks.audit.mock.calls[0]);
    expect(logged).toContain('price_delta_viewed');
    expect(logged).not.toMatch(/1000|1500|1600|price_rounded|cost/);
  });
  it('withholds a result that does not declare persist false or names another identity', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/commercial/price/route');
    for (const patch of [{ persist: true }, { project_ref: 'beta' }, { alternative_option_ref: 'dev_test_prod' }]) {
      mocks.engine.mockResolvedValueOnce({ ok: true, value: { ...result(), ...patch } });
      expect((await GET(url(valid), context)).status).toBe(409);
    }
    expect(mocks.audit).not.toHaveBeenCalled();
  });
});
