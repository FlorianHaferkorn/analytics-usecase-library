// @vitest-environment node
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/lib/auth/require-role', () => ({ requireRole: vi.fn() }));
import { requireRole } from '@/lib/auth/require-role';
import { requireRunnerAccess, runnerAccessReadiness, runnerAccessReadinessFailure } from '@/lib/auth/runner-access';
import type { SessionUser } from '@/lib/auth/session';

const NOW = 1_800_000_000_000;
const ORIGIN = 'https://studio.example.com';
const user: SessionUser = {
  id: 'admin', email: 'admin@example.com', name: 'Admin',
  authentication: { provider: 'github', providerAccountId: '12345', method: 'oauth', authenticatedAt: NOW },
};
function request(headers: Record<string, string> = {}) {
  return new Request(`${ORIGIN}/api/projects/project-1/runner`, {
    method: 'POST', headers: { origin: ORIGIN, 'content-type': 'application/json', ...headers },
  });
}
function session(authentication: SessionUser['authentication']) {
  vi.mocked(requireRole).mockResolvedValue([{ ...user, authentication }, null]);
}

describe('protected runner authentication and request boundary', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.spyOn(Date, 'now').mockReturnValue(NOW);
    vi.stubEnv('STUDIO_RUNNER_ORIGIN', ORIGIN);
    vi.stubEnv('AUTH_SECRET', 'eF4vM2wZ0pQ8nS6rL3jB9hD1uX7cA5tK');
    session(user.authentication);
  });
  afterEach(() => { vi.restoreAllMocks(); vi.unstubAllEnvs(); });

  it('uses current project admin authorization before any configuration or provenance checks', async () => {
    const response = new Response(null, { status: 401 });
    vi.mocked(requireRole).mockResolvedValue([null, response]);
    expect(await requireRunnerAccess('project-1', request(), true)).toEqual([null, response]);
    expect(requireRole).toHaveBeenCalledWith('admin', 'project-1');
  });
  it('preserves forbidden project membership', async () => {
    const response = new Response(null, { status: 403 });
    vi.mocked(requireRole).mockResolvedValue([null, response]);
    expect(await requireRunnerAccess('foreign')).toEqual([null, response]);
  });
  it.each(['', 'short-secret', 'changeme-this-is-not-a-secure-production-secret', 'your-secret-here-that-is-more-than-32-characters', 'a'.repeat(64)])('rejects insecure session secret configuration for reads and writes', async secret => {
    vi.stubEnv('AUTH_SECRET', secret);
    for (const mutation of [false, true]) {
      expect((await requireRunnerAccess('project-1', request(), mutation))[1]?.status).toBe(503);
    }
  });
  it('accepts the legacy configured secret name only when AUTH_SECRET is absent', async () => {
    vi.stubEnv('NEXTAUTH_SECRET', 'kR7aS2tM9vW3nX8cJ0hL5pQ1bD6eF4uZ');
    vi.stubEnv('AUTH_SECRET', undefined);
    expect((await requireRunnerAccess('project-1'))[1]).toBeNull();
    vi.stubEnv('AUTH_SECRET', '');
    expect((await requireRunnerAccess('project-1'))[1]?.status).toBe(503);
  });
  it.each([
    ['legacy', undefined],
    ['demo', { ...user.authentication!, provider: 'credentials', method: 'credentials' }],
    ['spoofed provider method', { ...user.authentication!, method: 'credentials' }],
    ['display-name actor', { ...user.authentication!, providerAccountId: 'admin@example.com' }],
    ['invalid future clock', { ...user.authentication!, authenticatedAt: NOW + 1 }],
    ['invalid clock type', { ...user.authentication!, authenticatedAt: 'today' as unknown as number }],
    ['missing clock', { ...user.authentication!, authenticatedAt: 0 }],
  ])('rejects %s sessions even when Studio is production', async (_label, authentication) => {
    vi.stubEnv('NODE_ENV', 'production');
    session(authentication);
    const [access, error] = await requireRunnerAccess('project-1', request(), true);
    expect(access).toBeNull(); expect(error?.status).toBe(403);
  });
  it('uses the immutable provider account ID, ignoring actor headers', async () => {
    const [access, error] = await requireRunnerAccess('project-1', request({ actor: 'github:999' }), true);
    expect(error).toBeNull(); expect(access?.actor).toBe('github:12345');
  });
  it('allows read-only access for an older verified sign-in but rejects mutation', async () => {
    session({ ...user.authentication!, authenticatedAt: NOW - 30 * 60 * 1000 - 1 });
    const [access] = await requireRunnerAccess('project-1');
    expect(access?.actor).toBe('github:12345');
    expect(runnerAccessReadiness(access!).find(check => check.id === 'studio_fresh_login')).toMatchObject({ state: 'missing', detail: expect.stringContaining('Read-only inspection') });
    expect((await requireRunnerAccess('project-1', request(), true))[1]?.status).toBe(403);
  });
  it('reports only local configured checks after protected access passes', async () => {
    const [access] = await requireRunnerAccess('project-1');
    const checks = runnerAccessReadiness(access!);
    expect(checks).toHaveLength(4);
    expect(checks.every(check => check.state === 'configured' && check.detail && check.action)).toBe(true);
    expect(checks.map(check => check.id)).toEqual(['studio_access', 'studio_session_secret', 'studio_fresh_login', 'studio_origin']);
    expect(JSON.stringify(checks)).not.toContain(process.env.AUTH_SECRET);
    expect(checks[0].action).toContain('does not verify Fabric permissions');
  });
  it.each([401, 403])('preserves the original %s error envelope and adds one safe access check', async status => {
    const body = { error: { code: status === 401 ? 'UNAUTHORIZED' : 'FORBIDDEN', message: 'Original access message' } };
    vi.mocked(requireRole).mockResolvedValue([null, Response.json(body, { status })]);
    const [, error] = await requireRunnerAccess('project-1');
    const enriched = await runnerAccessReadinessFailure(error!);
    const diagnostic = await enriched.json();
    expect(enriched.status).toBe(status);
    expect(enriched.headers.get('cache-control')).toBe('private, no-store');
    expect(diagnostic.error).toEqual(body.error);
    expect(diagnostic.checks).toHaveLength(1);
    expect(diagnostic.checks[0]).toMatchObject({ id: 'studio_access', state: 'missing' });
    expect(Number.isNaN(Date.parse(diagnostic.checked_at))).toBe(false);
  });
  it('exposes no configured secret when host signing configuration blocks access', async () => {
    vi.stubEnv('AUTH_SECRET', 'a'.repeat(64));
    const [, error] = await requireRunnerAccess('project-1');
    const diagnostic = await (await runnerAccessReadinessFailure(error!)).json();
    expect(diagnostic.checks).toHaveLength(1);
    expect(diagnostic.checks[0]).toMatchObject({ id: 'studio_session_secret', state: 'missing' });
    expect(JSON.stringify(diagnostic)).not.toContain('a'.repeat(64));
    expect(diagnostic.error.message).toContain('session secret');
  });
  it('distinguishes a demo session from a project permission failure without revealing host configuration', async () => {
    session(undefined);
    const [, error] = await requireRunnerAccess('project-1');
    const diagnostic = await (await runnerAccessReadinessFailure(error!)).json();
    expect(diagnostic.checks).toHaveLength(1);
    expect(diagnostic.checks[0].detail).toContain('Demo and legacy sessions');
    expect(JSON.stringify(diagnostic)).not.toContain('STUDIO_RUNNER_ORIGIN');
  });
  it.each<Record<string, string>>([
    { origin: 'https://attacker.example' },
    { origin: 'null' },
    { origin: '' },
    { 'sec-fetch-site': 'cross-site' },
    { 'content-type': 'text/plain' },
    { 'content-type': '' },
    { origin: 'https://attacker.example', host: 'attacker.example', 'x-forwarded-host': 'attacker.example' },
  ])('rejects untrusted request headers %j', async headers => {
    expect((await requireRunnerAccess('project-1', request(headers), true))[1]?.status).toBe(403);
  });
  it('rejects a missing mutation request', async () => {
    expect((await requireRunnerAccess('project-1', undefined, true))[1]?.status).toBe(403);
  });
  it.each(['', 'https://studio.example.com/', 'https://studio.example.com/path', 'https://user@studio.example.com', 'file:///tmp', 'https://studio.example.com?x=1', 'http://studio.example.com', 'http://192.168.1.10'])('fails closed on invalid host origin %s', async value => {
    vi.stubEnv('STUDIO_RUNNER_ORIGIN', value);
    const [access] = await requireRunnerAccess('project-1');
    expect(access).not.toBeNull();
    expect(runnerAccessReadiness(access!).find(check => check.id === 'studio_origin')).toMatchObject({ state: 'missing', action: expect.stringContaining('STUDIO_RUNNER_ORIGIN') });
    expect((await requireRunnerAccess('project-1', request(), true))[1]?.status).toBe(503);
  });
  it.each(['http://localhost:3000', 'http://127.0.0.1:3000', 'http://[::1]:3000'])('allows explicit loopback development origin %s', async value => {
    vi.stubEnv('STUDIO_RUNNER_ORIGIN', value);
    expect((await requireRunnerAccess('project-1', request({ origin: value }), true))[1]).toBeNull();
  });
  it('accepts JSON charset and exact origin with same-origin fetch metadata', async () => {
    expect((await requireRunnerAccess('project-1', request({ 'content-type': 'application/json; charset=utf-8', 'sec-fetch-site': 'same-origin' }), true))[1]).toBeNull();
  });
});
