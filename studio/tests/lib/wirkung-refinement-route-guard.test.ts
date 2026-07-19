/**
 * Route-level RBAC guard tests for POST /api/wirkung/refinements.
 *
 * Critical: both `approve` AND `reject` are terminal governance decisions and must
 * require admin. GET (list) requires only viewer role.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

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

import { GET, POST } from '@/app/api/wirkung/refinements/route';

const ADMIN_USER = { email: 'admin@co.com', name: 'Admin' };
const NON_ADMIN_USER = { email: 'user@co.com', name: 'User' };

function makePostRequest(body: object): Request {
  return new Request('http://localhost/api/wirkung/refinements', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  mockFindOrCreateUser.mockReturnValue({ id: 'user-1' });
  mockDecideRefinement.mockReturnValue({ proposalKey: 'k1', status: 'approved' });
  mockListRefinements.mockReturnValue([]);
});

describe('POST /api/wirkung/refinements — RBAC guard', () => {
  it('returns 401 when not authenticated', async () => {
    mockRequireAuth.mockResolvedValue([null, new Response(null, { status: 401 })]);
    const res = await POST(makePostRequest({ proposalKey: 'k1', action: 'approve' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin tries to approve', async () => {
    mockRequireAuth.mockResolvedValue([NON_ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(false);
    const res = await POST(makePostRequest({ proposalKey: 'k1', action: 'approve' }));
    expect(res.status).toBe(403);
    expect(mockDecideRefinement).not.toHaveBeenCalled();
  });

  it('returns 403 when non-admin tries to reject', async () => {
    mockRequireAuth.mockResolvedValue([NON_ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(false);
    const res = await POST(makePostRequest({ proposalKey: 'k1', action: 'reject' }));
    expect(res.status).toBe(403);
    expect(mockDecideRefinement).not.toHaveBeenCalled();
  });

  it('returns 200 when admin approves', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(true);
    const res = await POST(makePostRequest({ proposalKey: 'k1', action: 'approve' }));
    expect(res.status).toBe(200);
    expect(mockDecideRefinement).toHaveBeenCalledWith('k1', 'approve', ADMIN_USER.email, '');
  });

  it('returns 200 when admin rejects', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(true);
    const res = await POST(makePostRequest({ proposalKey: 'k1', action: 'reject' }));
    expect(res.status).toBe(200);
    expect(mockDecideRefinement).toHaveBeenCalledWith('k1', 'reject', ADMIN_USER.email, '');
  });
});

describe('GET /api/wirkung/refinements — viewer access', () => {
  it('returns 200 with proposals list for viewer', async () => {
    mockRequireRole.mockResolvedValue([{ email: 'viewer@co.com' }, null]);
    mockListRefinements.mockReturnValue([{ proposalKey: 'k1', status: 'pending' }]);
    const res = await GET();
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json).toEqual({ proposals: [{ proposalKey: 'k1', status: 'pending' }] });
  });
});
