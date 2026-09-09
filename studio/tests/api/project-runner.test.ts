import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
const mocks = vi.hoisted(() => ({ guard: vi.fn(), host: vi.fn() }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: vi.fn() }));
vi.mock('@/lib/auth/runner-access', async importOriginal => ({ ...await importOriginal<typeof import('@/lib/auth/runner-access')>(), requireRunnerAccess: mocks.guard }));
vi.mock('@/lib/bridge/project-runner', () => ({ projectRunner: mocks.host }));
const hash = 'a'.repeat(64), approval = 'b'.repeat(64), planHash = 'c'.repeat(64);
const context = { params: Promise.resolve({ projectId: 'alpha' }) };
const plan = { project_ref: 'alpha', revision_hash: hash, plan_sha256: planHash };
const body = { mode: 'approve', revisionHash: hash, plan, rationale: 'Explicit target plan reviewed by the operator.', confirmed: true };
const post = (value: unknown) => new Request('https://studio.test/api', { method: 'POST', headers: { origin: 'https://studio.test', 'content-type': 'application/json' }, body: JSON.stringify(value) });
const receipt = { project_ref: 'alpha', revision_hash: hash, approval_id: approval, plan_sha256: planHash };
beforeEach(() => { vi.clearAllMocks(); vi.stubEnv('STUDIO_RUNNER_ORIGIN', 'https://studio.test'); mocks.guard.mockResolvedValue([{ actor: 'github:1234', authentication: { authenticatedAt: Date.now() } }, null]); mocks.host.mockResolvedValue({ ok: true, value: receipt }); });
afterEach(() => vi.unstubAllEnvs());
describe('Protected runner routes', () => {
  it('denies before reading or invoking any host capability', async () => {
    const error = { code: 'FORBIDDEN', message: 'Project administrator access required' };
    mocks.guard.mockResolvedValue([null, Response.json({ error }, { status: 403 })]);
    const { GET, POST } = await import('@/app/api/projects/[projectId]/runner/route');
    const response = await GET(new Request(`https://studio.test?revision=${hash}`), context);
    expect(response.status).toBe(403);
    const diagnostic = await response.json();
    expect(diagnostic.error).toEqual(error);
    expect(diagnostic.checks).toHaveLength(1);
    expect(diagnostic.checks[0]).toMatchObject({ id: 'studio_access', state: 'missing' });
    expect(Number.isNaN(Date.parse(diagnostic.checked_at))).toBe(false);
    const mutation = await POST(post(body), context);
    expect(mutation.status).toBe(403);
    expect(await mutation.json()).toEqual({ error });
    expect(mocks.host).not.toHaveBeenCalled();
  });
  it('merges authenticated Studio and host checks with a response timestamp', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/runner/route');
    const hostCheck = { id: 'runner_enabled', title: 'Runner enabled', state: 'missing', detail: 'The host runner is disabled.', action: 'Review the private host configuration.' };
    mocks.host.mockResolvedValue({ ok: true, value: { project_ref: 'alpha', can_approve: true, can_execute: true, checks: [hostCheck] } });
    const response = await GET(new Request(`https://studio.test?revision=${hash}`), context);
    const diagnostic = await response.json();
    expect(response.status).toBe(200);
    expect(diagnostic.checks).toHaveLength(5);
    expect(diagnostic.checks[0]).toMatchObject({ id: 'studio_access', state: 'configured' });
    expect(diagnostic.checks.at(-1)).toEqual(hostCheck);
    expect(diagnostic).toMatchObject({ can_approve: true, can_execute: true });
    expect(Number.isNaN(Date.parse(diagnostic.checked_at))).toBe(false);
    expect(mocks.guard).toHaveBeenCalledWith('alpha');
    expect(mocks.host).toHaveBeenCalledExactlyOnceWith('alpha', hash, 'github:1234', { mode: 'status' });
  });
  it('keeps status readable for an old OAuth login and diagnoses missing renewal', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/runner/route');
    mocks.guard.mockResolvedValue([{ actor: 'github:1234', authentication: { authenticatedAt: Date.now() - 31 * 60 * 1000 } }, null]);
    mocks.host.mockResolvedValue({ ok: true, value: { project_ref: 'alpha', can_approve: true, can_execute: true, checks: [] } });
    const response = await GET(new Request(`https://studio.test?revision=${hash}`), context);
    expect(response.status).toBe(200);
    const diagnostic = await response.json();
    expect(diagnostic.checks).toContainEqual(expect.objectContaining({ id: 'studio_fresh_login', state: 'missing' }));
    expect(diagnostic).toMatchObject({ can_approve: false, can_execute: false });
    expect(mocks.host).toHaveBeenCalledTimes(1);
  });
  it('retains authenticated readiness diagnostics when the private host check fails', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/runner/route');
    const error = 'Protected runner request refused. Check host configuration, exact scope and signed approval evidence.';
    mocks.host.mockResolvedValue({ ok: false, status: 409, error });
    const response = await GET(new Request(`https://studio.test?revision=${hash}`), context);
    expect(response.status).toBe(409);
    const diagnostic = await response.json();
    expect(diagnostic.error).toBe(error);
    expect(diagnostic.checks).toHaveLength(5);
    expect(diagnostic.checks[0]).toMatchObject({ id: 'studio_access', state: 'configured' });
    expect(diagnostic.checks.at(-1)).toMatchObject({ id: 'runner_host', state: 'missing', action: expect.stringContaining('configured Python runtime') });
    expect(Number.isNaN(Date.parse(diagnostic.checked_at))).toBe(false);
    expect(mocks.host).toHaveBeenCalledExactlyOnceWith('alpha', hash, 'github:1234', { mode: 'status' });
  });
  it('keeps an invalid origin diagnostic read-only and disables advertised mutations', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/runner/route');
    vi.stubEnv('STUDIO_RUNNER_ORIGIN', 'http://remote.example.test');
    mocks.host.mockResolvedValue({ ok: true, value: { project_ref: 'alpha', can_approve: true, can_execute: true, checks: [] } });
    const response = await GET(new Request(`https://studio.test?revision=${hash}`), context);
    expect(response.status).toBe(200);
    const diagnostic = await response.json();
    expect(diagnostic.checks).toContainEqual(expect.objectContaining({ id: 'studio_origin', state: 'missing' }));
    expect(diagnostic).toMatchObject({ can_approve: false, can_execute: false });
    expect(mocks.host).toHaveBeenCalledTimes(1);
  });
  it('checks mutation origin and authentication through the guard', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/runner/route');
    const request = post(body);
    expect((await POST(request, context)).status).toBe(200);
    expect(mocks.guard).toHaveBeenCalledWith('alpha', request, true);
    expect(mocks.host).toHaveBeenCalledWith('alpha', hash, 'github:1234', { mode: 'approve', plan, rationale: body.rationale });
  });
  it('rejects caller authority, commands, foreign plan and unconfirmed intent', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/runner/route');
    for (const patch of [{ actor: 'github:admin' }, { command: 'fab rm' }, { config: '../file' }, { plan: { ...plan, project_ref: 'beta' } }, { confirmed: false }, { rationale: 'yes' }]) {
      expect((await POST(post({ ...body, ...patch }), context)).status).toBe(422);
    }
    expect(mocks.host).not.toHaveBeenCalled();
  });
  it('executes only a stored approval ID and version, not a pasted plan', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/runner/route');
    const execute = { mode: 'execute', revisionHash: hash, approvalId: approval, confirmed: true };
    expect((await POST(post({ ...execute, plan }), context)).status).toBe(422);
    expect((await POST(post(execute), context)).status).toBe(200);
    expect(mocks.host).toHaveBeenCalledWith('alpha', hash, 'github:1234', { mode: 'execute', approvalId: approval });
  });
  it('reports an uncertain execution without issuing another command', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/runner/route');
    mocks.host.mockResolvedValue({ ok: false, status: 503, error: 'Outcome uncertain; retrieve evidence' });
    expect((await POST(post({ mode: 'execute', revisionHash: hash, approvalId: approval, confirmed: true }), context)).status).toBe(503);
    expect(mocks.host).toHaveBeenCalledTimes(1);
  });
  it('reads signed evidence without executing or requiring current HEAD', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/runner/route');
    mocks.host.mockResolvedValue({ ok: true, value: { status: 'completed', receipt } });
    const response = await GET(new Request(`https://studio.test?revision=${hash}&approval=${approval}`), context);
    expect(response.status).toBe(200);
    expect(response.headers.get('cache-control')).toBe('private, no-store');
    expect(mocks.host).toHaveBeenCalledWith('alpha', hash, 'github:1234', { mode: 'outcome', approvalId: approval });
  });
  it('rejects saved evidence for another revision', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/runner/route');
    mocks.host.mockResolvedValue({ ok: true, value: { status: 'completed', receipt: { ...receipt, revision_hash: approval } } });
    expect((await GET(new Request(`https://studio.test?revision=${hash}&approval=${approval}`), context)).status).toBe(409);
  });
  it('rejects unpinned, oversized and malformed requests', async () => {
    const { GET, POST } = await import('@/app/api/projects/[projectId]/runner/route');
    expect((await GET(new Request('https://studio.test'), context)).status).toBe(422);
    expect((await POST(post({ ...body, rationale: 'x'.repeat(2_000_001) }), context)).status).toBe(413);
    expect((await POST(post(null), context)).status).toBe(422);
    expect((await POST(new Request('https://studio.test', { method: 'POST', body: '{' }), context)).status).toBe(400);
    expect(mocks.host).not.toHaveBeenCalled();
  });
});
