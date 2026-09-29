import { beforeEach, describe, expect, it, vi } from 'vitest';
const mocks = vi.hoisted(() => ({ role: vi.fn(), engine: vi.fn(), audit: vi.fn() }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: mocks.role }));
vi.mock('@/lib/bridge/project-staffing', () => ({ projectStaffing: mocks.engine }));
vi.mock('@/lib/db/audit-repo', () => ({ logAuditEvent: mocks.audit }));
const hash = 'a'.repeat(64);
const context = { params: Promise.resolve({ projectId: 'alpha' }) };
const url = (query: string) => new Request(`http://x/staffing?${query}`);
const valid = `revision=${hash}&decision=decision_environment_model&option=dev_prod`;
const side = { classes: [{ rate_class: 'engineer_nearshore', hours: 26, weekly_capacity: 30, weeks: 0.87, earliest_full_team: null, people: [{ name: 'Person Alpha', hours: 17.33, hours_per_week: 20 }] }], gaps: [], weeks_in_parallel: 0.87, people: ['Person Alpha'] };
const result = () => ({ project_ref: 'alpha', baseline_revision_hash: hash, decision_ref: 'decision_environment_model', alternative_option_ref: 'dev_prod',
  status: 'evaluated', personal_data: true, persist: false, roster_fingerprint_sha256: 'f'.repeat(64),
  baseline: side, alternative: side, delta: { weeks_in_parallel: { before: 1, after: 0.87 }, people_no_longer_needed: [], people_newly_needed: [], new_gaps: [] } });
beforeEach(() => {
  vi.clearAllMocks();
  mocks.role.mockResolvedValue([{ email: 'admin@example.test' }, null]);
  mocks.engine.mockResolvedValue({ ok: true, value: result() });
});
describe('Named staffing API', () => {
  it('requires the admin role before evaluating', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/commercial/staffing/route');
    mocks.role.mockResolvedValue([null, new Response('denied', { status: 403 })]);
    expect((await GET(url(valid), context)).status).toBe(403);
    expect(mocks.role).toHaveBeenCalledWith('admin', 'alpha');
    expect(mocks.engine).not.toHaveBeenCalled();
  });
  it('requires pinned identifiers and never allows caching', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/commercial/staffing/route');
    for (const query of ['', `revision=HEAD&decision=d&option=o`, `revision=${hash}&decision=D&option=dev_prod`]) {
      expect((await GET(url(query), context)).status).toBe(422);
    }
    const response = await GET(url(valid), context);
    expect(response.status).toBe(200);
    expect(response.headers.get('cache-control')).toBe('private, no-store');
  });
  it('audits the view without any name', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/commercial/staffing/route');
    await GET(url(valid), context);
    expect(mocks.audit).toHaveBeenCalledOnce();
    const logged = JSON.stringify(mocks.audit.mock.calls[0]);
    expect(logged).toContain('staffing_viewed');
    expect(logged).not.toMatch(/Person Alpha|engineer_nearshore/);
  });
  it('withholds a result that does not declare persist false or names another identity', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/commercial/staffing/route');
    for (const patch of [{ persist: true }, { project_ref: 'beta' }, { alternative_option_ref: 'dev_test_prod' }]) {
      mocks.engine.mockResolvedValueOnce({ ok: true, value: { ...result(), ...patch } });
      expect((await GET(url(valid), context)).status).toBe(409);
    }
    expect(mocks.audit).not.toHaveBeenCalled();
  });
});
