/**
 * Route-level guard tests for POST /api/wirkung/refinements.
 *
 * Verifies that both `approve` and `reject` (terminal governance decisions)
 * require admin RBAC, while GET (list) only requires viewer.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

const { mockRequireAuth, mockRequireRole, mockCheckAccess, mockFindOrCreateUser, mockDecideRefinement, mockListRefinements } = vi.hoisted(() => ({
  mockRequireAuth: vi.fn(),
  mockRequireRole: vi.fn(),
  mockCheckAccess: vi.fn(),
  mockFindOrCreateUser: vi.fn(),
  mockDecideRefinement: vi.fn(),
  mockListRefinements: vi.fn(),
}));

vi.mock('@/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: mockRequireRole }));
vi.mock('@/lib/db/rbac-repo', () => ({ checkAccess: mockCheckAccess }));
vi.mock('@/lib/db/user-repo', () => ({ findOrCreateUser: mockFindOrCreateUser }));
vi.mock('@/lib/governance/refinement-workflow', () => ({
  decideRefinement: mockDecideRefinement,
  listRefinements: mockListRefinements,
}));

import { GET, POST } from '../../src/app/api/wirkung/refinements/route';

const ADMIN_USER = { id: 'u1', email: 'admin@co.com', name: 'Admin' };
const NON_ADMIN_USER = { id: 'u2', email: 'user@co.com', name: 'User' };
const DB_USER = { id: 42 };
const PROPOSAL_RECORD = { proposal_key: 'AC-001::KPI-001', status: 'approved' };

function buildRequest(body: Record<string, unknown>): Request {
  return new Request('http://localhost/api/wirkung/refinements', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  mockFindOrCreateUser.mockReturnValue(DB_USER);
  mockDecideRefinement.mockReturnValue(PROPOSAL_RECORD);
  mockListRefinements.mockReturnValue([]);
});

describe('POST /api/wirkung/refinements — auth guard', () => {
  it('returns 401 when unauthenticated', async () => {
    mockRequireAuth.mockResolvedValue([null, new Response('', { status: 401 })]);

    const res = await POST(buildRequest({ proposalKey: 'AC-001::KPI-001', action: 'approve' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin tries to approve', async () => {
    mockRequireAuth.mockResolvedValue([NON_ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(false);

    const res = await POST(buildRequest({ proposalKey: 'AC-001::KPI-001', action: 'approve' }));
    expect(res.status).toBe(403);
    expect(mockCheckAccess).toHaveBeenCalledWith('default', DB_USER.id, 'admin');
  });

  it('returns 403 when non-admin tries to reject', async () => {
    mockRequireAuth.mockResolvedValue([NON_ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(false);

    const res = await POST(buildRequest({ proposalKey: 'AC-001::KPI-001', action: 'reject' }));
    expect(res.status).toBe(403);
    expect(mockCheckAccess).toHaveBeenCalledWith('default', DB_USER.id, 'admin');
  });

  it('succeeds (200) when admin approves', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(true);

    const res = await POST(buildRequest({ proposalKey: 'AC-001::KPI-001', action: 'approve' }));
    expect(res.status).toBe(200);
    const body = await res.json() as { proposal: unknown };
    expect(body.proposal).toEqual(PROPOSAL_RECORD);
  });

  it('succeeds (200) when admin rejects', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(true);

    const res = await POST(buildRequest({ proposalKey: 'AC-001::KPI-001', action: 'reject' }));
    expect(res.status).toBe(200);
    const body = await res.json() as { proposal: unknown };
    expect(body.proposal).toEqual(PROPOSAL_RECORD);
  });
});

describe('GET /api/wirkung/refinements — viewer access', () => {
  it('returns proposals list for viewer-level access', async () => {
    const PROPOSALS = [{ proposal_key: 'AC-001::KPI-001', status: 'pending_review' }];
    mockRequireRole.mockResolvedValue([ADMIN_USER, null]);
    mockListRefinements.mockReturnValue(PROPOSALS);

    const res = await GET();
    expect(res.status).toBe(200);
    const body = await res.json() as { proposals: unknown };
    expect(body.proposals).toEqual(PROPOSALS);
  });
});
