/**
 * Route-level auth guard tests for POST /api/wirkung/refinements.
 * Verifies that `reject` (as well as `approve`) requires admin RBAC.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockRequireAuth = vi.hoisted(() => vi.fn());
const mockRequireRole = vi.hoisted(() => vi.fn());
const mockCheckAccess = vi.hoisted(() => vi.fn());
const mockFindOrCreateUser = vi.hoisted(() => vi.fn());
const mockDecideRefinement = vi.hoisted(() => vi.fn());
const mockListRefinements = vi.hoisted(() => vi.fn());

vi.mock('@/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: mockRequireRole }));
vi.mock('@/lib/db/rbac-repo', () => ({ checkAccess: mockCheckAccess }));
vi.mock('@/lib/db/user-repo', () => ({ findOrCreateUser: mockFindOrCreateUser }));
vi.mock('@/lib/governance/refinement-workflow', () => ({
  decideRefinement: mockDecideRefinement,
  listRefinements: mockListRefinements,
}));

async function importRoute() {
  const mod = await import('@/app/api/wirkung/refinements/route');
  return mod;
}

function makePostRequest(body: Record<string, unknown>): Request {
  return new Request('http://localhost/api/wirkung/refinements', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

describe('POST /api/wirkung/refinements — auth guard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns 401 when unauthenticated', async () => {
    mockRequireAuth.mockResolvedValue([null, new Response('', { status: 401 })]);
    const { POST } = await importRoute();
    const res = await POST(makePostRequest({ proposalKey: 'k1', action: 'approve' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 for non-admin attempting approve', async () => {
    mockRequireAuth.mockResolvedValue([{ email: 'user@test.com', name: 'User' }, null]);
    mockFindOrCreateUser.mockReturnValue({ id: 'u1' });
    mockCheckAccess.mockReturnValue(false);
    const { POST } = await importRoute();
    const res = await POST(makePostRequest({ proposalKey: 'k1', action: 'approve' }));
    expect(res.status).toBe(403);
  });

  it('returns 403 for non-admin attempting reject', async () => {
    mockRequireAuth.mockResolvedValue([{ email: 'user@test.com', name: 'User' }, null]);
    mockFindOrCreateUser.mockReturnValue({ id: 'u1' });
    mockCheckAccess.mockReturnValue(false);
    const { POST } = await importRoute();
    const res = await POST(makePostRequest({ proposalKey: 'k1', action: 'reject' }));
    expect(res.status).toBe(403);
  });

  it('allows admin to approve', async () => {
    mockRequireAuth.mockResolvedValue([{ email: 'admin@test.com', name: 'Admin' }, null]);
    mockFindOrCreateUser.mockReturnValue({ id: 'a1' });
    mockCheckAccess.mockReturnValue(true);
    mockDecideRefinement.mockReturnValue({ proposalKey: 'k1', status: 'approved' });
    const { POST } = await importRoute();
    const res = await POST(makePostRequest({ proposalKey: 'k1', action: 'approve' }));
    expect(res.status).toBe(200);
  });

  it('allows admin to reject', async () => {
    mockRequireAuth.mockResolvedValue([{ email: 'admin@test.com', name: 'Admin' }, null]);
    mockFindOrCreateUser.mockReturnValue({ id: 'a1' });
    mockCheckAccess.mockReturnValue(true);
    mockDecideRefinement.mockReturnValue({ proposalKey: 'k1', status: 'rejected' });
    const { POST } = await importRoute();
    const res = await POST(makePostRequest({ proposalKey: 'k1', action: 'reject' }));
    expect(res.status).toBe(200);
  });

  it('allows viewer to GET proposals', async () => {
    mockRequireRole.mockResolvedValue([{ email: 'viewer@test.com' }, null]);
    mockListRefinements.mockReturnValue([]);
    const { GET } = await importRoute();
    const res = await GET();
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data).toHaveProperty('proposals');
  });
});
