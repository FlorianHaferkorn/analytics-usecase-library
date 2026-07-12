/**
 * Route-level guard tests for POST /api/wirkung/refinements.
 *
 * Verifies that approve AND reject both require admin (the reject bypass was a
 * governance vulnerability: only approve was guarded, leaving reject — a terminal
 * action — reachable by any authenticated user, permanently closing proposals).
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

const { mockRequireAuth, mockRequireRole, mockCheckAccess, mockFindOrCreateUser, mockDecideRefinement, mockListRefinements } =
  vi.hoisted(() => ({
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

import { POST, GET } from '@/app/api/wirkung/refinements/route';

const AUTHED_USER = { email: 'user@test.com', name: 'Test User' };
const DB_USER = { id: 'usr-1', email: 'user@test.com', name: 'Test User' };
const PROPOSAL_RECORD = { proposalKey: 'p-1', status: 'approved' };

function makePostRequest(body: object): Request {
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

describe('POST /api/wirkung/refinements — admin guard', () => {
  it('returns 401 when unauthenticated', async () => {
    const authErr = new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
    mockRequireAuth.mockResolvedValue([null, authErr]);

    const res = await POST(makePostRequest({ proposalKey: 'p-1', action: 'approve' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin attempts approve', async () => {
    mockRequireAuth.mockResolvedValue([AUTHED_USER, null]);
    mockCheckAccess.mockReturnValue(undefined); // not admin

    const res = await POST(makePostRequest({ proposalKey: 'p-1', action: 'approve' }));
    expect(res.status).toBe(403);
    expect(mockDecideRefinement).not.toHaveBeenCalled();
  });

  it('returns 403 when non-admin attempts reject (governance bypass fix)', async () => {
    mockRequireAuth.mockResolvedValue([AUTHED_USER, null]);
    mockCheckAccess.mockReturnValue(undefined); // not admin

    const res = await POST(makePostRequest({ proposalKey: 'p-1', action: 'reject' }));
    expect(res.status).toBe(403);
    expect(mockDecideRefinement).not.toHaveBeenCalled();
  });

  it('returns 200 when admin approves', async () => {
    mockRequireAuth.mockResolvedValue([AUTHED_USER, null]);
    mockCheckAccess.mockReturnValue({ id: 'usr-1', role: 'admin' }); // is admin

    const res = await POST(makePostRequest({ proposalKey: 'p-1', action: 'approve' }));
    expect(res.status).toBe(200);
    expect(mockDecideRefinement).toHaveBeenCalledWith('p-1', 'approve', AUTHED_USER.email, '');
  });

  it('returns 200 when admin rejects', async () => {
    mockRequireAuth.mockResolvedValue([AUTHED_USER, null]);
    mockCheckAccess.mockReturnValue({ id: 'usr-1', role: 'admin' }); // is admin

    const res = await POST(makePostRequest({ proposalKey: 'p-1', action: 'reject' }));
    expect(res.status).toBe(200);
    expect(mockDecideRefinement).toHaveBeenCalledWith('p-1', 'reject', AUTHED_USER.email, '');
  });
});

describe('GET /api/wirkung/refinements — viewer access', () => {
  it('returns 200 with proposal list for authenticated viewer', async () => {
    mockRequireRole.mockResolvedValue([AUTHED_USER, null]);
    mockListRefinements.mockReturnValue([PROPOSAL_RECORD]);

    const res = await GET();
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.proposals).toHaveLength(1);
  });
});
