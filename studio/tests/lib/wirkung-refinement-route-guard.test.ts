/**
 * Route-level guard tests for POST /api/wirkung/refinements
 * Verifies that admin RBAC is enforced for both `approve` and `reject` actions.
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

const { GET, POST } = await import('@/app/api/wirkung/refinements/route');

const USER = { email: 'user@test.com', name: 'Test User' };
const DB_USER = { id: 'user-1' };

function makeRequest(body: object): Request {
  return new Request('http://localhost/api/wirkung/refinements', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  mockFindOrCreateUser.mockReturnValue(DB_USER);
  mockDecideRefinement.mockReturnValue({ proposalKey: 'k1', status: 'approved' });
  mockListRefinements.mockReturnValue([]);
});

describe('POST /api/wirkung/refinements — auth guard', () => {
  it('returns 401 when unauthenticated', async () => {
    const authErr = new Response('Unauthorized', { status: 401 });
    mockRequireAuth.mockResolvedValue([null, authErr]);
    const res = await POST(makeRequest({ proposalKey: 'k1', action: 'approve' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin tries to approve', async () => {
    mockRequireAuth.mockResolvedValue([USER, null]);
    mockCheckAccess.mockReturnValue(false);
    const res = await POST(makeRequest({ proposalKey: 'k1', action: 'approve' }));
    expect(res.status).toBe(403);
  });

  it('returns 403 when non-admin tries to reject', async () => {
    mockRequireAuth.mockResolvedValue([USER, null]);
    mockCheckAccess.mockReturnValue(false);
    const res = await POST(makeRequest({ proposalKey: 'k1', action: 'reject' }));
    expect(res.status).toBe(403);
  });

  it('returns 200 when admin approves', async () => {
    mockRequireAuth.mockResolvedValue([USER, null]);
    mockCheckAccess.mockReturnValue(true);
    const res = await POST(makeRequest({ proposalKey: 'k1', action: 'approve' }));
    expect(res.status).toBe(200);
  });

  it('returns 200 when admin rejects', async () => {
    mockRequireAuth.mockResolvedValue([USER, null]);
    mockCheckAccess.mockReturnValue(true);
    const res = await POST(makeRequest({ proposalKey: 'k1', action: 'reject' }));
    expect(res.status).toBe(200);
  });

  it('returns 200 for GET with viewer role', async () => {
    mockRequireRole.mockResolvedValue([USER, null]);
    const res = await GET();
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json).toHaveProperty('proposals');
  });
});
