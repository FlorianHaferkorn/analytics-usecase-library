/**
 * Route-level auth guard tests for POST /api/ai-config.
 * Verifies that `reopen` (as well as `approve`) requires admin RBAC.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockRequireAuth = vi.hoisted(() => vi.fn());
const mockCheckAccess = vi.hoisted(() => vi.fn());
const mockFindOrCreateUser = vi.hoisted(() => vi.fn());
const mockGetConfigLayer = vi.hoisted(() => vi.fn());
const mockUpsertConfigLayer = vi.hoisted(() => vi.fn());
const mockTransitionConfigLayer = vi.hoisted(() => vi.fn());

vi.mock('@/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));
vi.mock('@/lib/db/rbac-repo', () => ({ checkAccess: mockCheckAccess }));
vi.mock('@/lib/db/user-repo', () => ({ findOrCreateUser: mockFindOrCreateUser }));
vi.mock('@/lib/db/ai-config-repo', () => ({
  getConfigLayer: mockGetConfigLayer,
  upsertConfigLayer: mockUpsertConfigLayer,
  transitionConfigLayer: mockTransitionConfigLayer,
  AiConfigGovernanceError: class AiConfigGovernanceError extends Error {},
}));

async function importRoute() {
  const { POST } = await import('@/app/api/ai-config/route');
  return POST;
}

function makeRequest(body: Record<string, unknown>): Request {
  return new Request('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

describe('POST /api/ai-config — auth guard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns 401 when unauthenticated', async () => {
    mockRequireAuth.mockResolvedValue([null, new Response('', { status: 401 })]);
    const POST = await importRoute();
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 for non-admin attempting approve', async () => {
    mockRequireAuth.mockResolvedValue([{ email: 'user@test.com', name: 'User' }, null]);
    mockFindOrCreateUser.mockReturnValue({ id: 'u1' });
    mockCheckAccess.mockReturnValue(false);
    const POST = await importRoute();
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('returns 403 for non-admin attempting reopen', async () => {
    mockRequireAuth.mockResolvedValue([{ email: 'user@test.com', name: 'User' }, null]);
    mockFindOrCreateUser.mockReturnValue({ id: 'u1' });
    mockCheckAccess.mockReturnValue(false);
    const POST = await importRoute();
    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('allows admin to approve', async () => {
    mockRequireAuth.mockResolvedValue([{ email: 'admin@test.com', name: 'Admin' }, null]);
    mockFindOrCreateUser.mockReturnValue({ id: 'a1' });
    mockCheckAccess.mockReturnValue(true);
    mockTransitionConfigLayer.mockReturnValue({ id: 'r1', status: 'approved' });
    const POST = await importRoute();
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(200);
  });

  it('allows admin to reopen', async () => {
    mockRequireAuth.mockResolvedValue([{ email: 'admin@test.com', name: 'Admin' }, null]);
    mockFindOrCreateUser.mockReturnValue({ id: 'a1' });
    mockCheckAccess.mockReturnValue(true);
    mockTransitionConfigLayer.mockReturnValue({ id: 'r1', status: 'draft' });
    const POST = await importRoute();
    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(200);
  });

  it('allows any authenticated user to submit', async () => {
    mockRequireAuth.mockResolvedValue([{ email: 'user@test.com', name: 'User' }, null]);
    mockTransitionConfigLayer.mockReturnValue({ id: 'r1', status: 'pending' });
    const POST = await importRoute();
    const res = await POST(makeRequest({ op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockCheckAccess).not.toHaveBeenCalled();
  });
});
