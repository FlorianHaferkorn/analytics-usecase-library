/**
 * Route-level guard tests for POST /api/wirkung/refinements.
 *
 * Verifies that:
 *  - unauthenticated requests receive 401
 *  - non-admin callers are blocked from `approve` AND `reject` (403)
 *  - admin callers may `approve` and `reject` (200)
 *  - authenticated viewers can GET the proposal list (200)
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

const AUTHED_USER = { email: 'user@test.local', name: 'User' };
const UNAUTHED = [null, new Response('Unauthorized', { status: 401 })] as const;
const AUTHED = [AUTHED_USER, null] as const;
const DB_USER = { id: 'user-1' };

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
  mockDecideRefinement.mockReturnValue({ proposalKey: 'k', status: 'approved' });
  mockListRefinements.mockReturnValue([]);
});

describe('GET /api/wirkung/refinements — viewer gate', () => {
  it('returns 200 with proposal list for authenticated viewer', async () => {
    mockRequireRole.mockResolvedValue(AUTHED);
    const res = await GET();
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty('proposals');
  });
});

describe('POST /api/wirkung/refinements — RBAC guard', () => {
  it('returns 401 when not authenticated', async () => {
    mockRequireAuth.mockResolvedValue(UNAUTHED);
    const res = await POST(makePostRequest({ proposalKey: 'k', action: 'approve' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin tries to approve', async () => {
    mockRequireAuth.mockResolvedValue(AUTHED);
    mockCheckAccess.mockReturnValue(null); // not admin
    const res = await POST(makePostRequest({ proposalKey: 'k', action: 'approve' }));
    expect(res.status).toBe(403);
  });

  it('returns 403 when non-admin tries to reject (regression guard)', async () => {
    mockRequireAuth.mockResolvedValue(AUTHED);
    mockCheckAccess.mockReturnValue(null); // not admin
    const res = await POST(makePostRequest({ proposalKey: 'k', action: 'reject' }));
    expect(res.status).toBe(403);
  });

  it('returns 200 when admin approves', async () => {
    mockRequireAuth.mockResolvedValue(AUTHED);
    mockCheckAccess.mockReturnValue({ role: 'admin' }); // admin
    const res = await POST(makePostRequest({ proposalKey: 'k', action: 'approve', justification: 'ok' }));
    expect(res.status).toBe(200);
  });

  it('returns 200 when admin rejects', async () => {
    mockRequireAuth.mockResolvedValue(AUTHED);
    mockCheckAccess.mockReturnValue({ role: 'admin' }); // admin
    const res = await POST(makePostRequest({ proposalKey: 'k', action: 'reject', justification: 'not ready' }));
    expect(res.status).toBe(200);
  });
});
