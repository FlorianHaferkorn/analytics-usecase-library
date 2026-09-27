import { beforeEach, describe, expect, it, vi } from 'vitest';

const h = vi.hoisted(() => ({ role: vi.fn(), run: vi.fn(), holds: vi.fn(), hold: vi.fn(), release: vi.fn() }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: h.role }));
vi.mock('@/lib/db/ai-retention', () => ({
  AiRetentionError: class extends Error {},
  activeLegalHolds: h.holds,
  placeLegalHold: h.hold,
  releaseLegalHold: h.release,
  runAiRetention: h.run,
  resolveAiRetentionPolicy: () => ({ policy: { egressMonths: 13 }, overridden: [] }),
}));

function post(body: unknown) {
  return new Request('http://local/api/audit/retention', {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body),
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  h.role.mockResolvedValue([{ email: 'admin@example.com' }, null]);
  h.run.mockReturnValue({ dry_run: true, projects: [] });
  h.holds.mockReturnValue([]);
});

describe('retention API', () => {
  it('GET is a dry run for admins only', async () => {
    const { GET } = await import('@/app/api/audit/retention/route');
    const response = await GET();
    expect(response.status).toBe(200);
    expect(h.role).toHaveBeenCalledWith('admin');
    expect(h.run).toHaveBeenCalledWith(expect.objectContaining({ dryRun: true }));
  });

  it('refuses a real run without explicit confirmation', async () => {
    const { POST } = await import('@/app/api/audit/retention/route');
    const response = await POST(post({ action: 'run' }));
    expect(response.status).toBe(400);
    expect(h.run).not.toHaveBeenCalled();
  });

  it('runs for real only with confirm: true', async () => {
    const { POST } = await import('@/app/api/audit/retention/route');
    const response = await POST(post({ action: 'run', confirm: true }));
    expect(response.status).toBe(200);
    expect(h.run).toHaveBeenCalledWith(expect.objectContaining({ dryRun: false }));
  });

  it('stops a non-admin before anything runs', async () => {
    h.role.mockResolvedValue([null, new Response(null, { status: 403 })]);
    const { POST } = await import('@/app/api/audit/retention/route');
    const response = await POST(post({ action: 'run', confirm: true }));
    expect(response.status).toBe(403);
    expect(h.run).not.toHaveBeenCalled();
  });

  it('places a legal hold under the admin identity', async () => {
    h.hold.mockReturnValue({ id: 'hold-1' });
    const { POST } = await import('@/app/api/audit/retention/route');
    const response = await POST(post({ action: 'hold', projectId: 'default', reference: 'CASE-1' }));
    expect(response.status).toBe(201);
    expect(h.hold).toHaveBeenCalledWith('default', 'CASE-1', 'admin@example.com');
  });
});
