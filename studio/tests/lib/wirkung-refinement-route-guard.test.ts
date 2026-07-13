/**
 * Route-level auth guard tests for GET/POST /api/wirkung/refinements.
 *
 * Verifies that `reject` (a terminal governance decision that permanently
 * closes a refinement proposal) is gated by the same admin RBAC check as
 * `approve`, and that GET (list) is accessible to any viewer.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

const {
  mockRequireAuth,
  mockRequireRole,
  mockCheckAccess,
  mockFindOrCreateUser,
  mockDecideRefinement,
  mockListRefinements,
} = vi.hoisted(() => ({
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

import { GET, POST } from '@/app/api/wirkung/refinements/route';

const ADMIN_USER = { id: 'u-admin', email: 'admin@co.com', name: 'Admin' };
const NORMAL_USER = { id: 'u-normal', email: 'user@co.com', name: 'User' };
const STUB_RECORD = { proposal_key: 'C-M2.1::margin.gm.pct', status: 'approved', decided_by: 'admin@co.com' };

function makePostRequest(body: Record<string, unknown>): Request {
  return new Request('http://localhost/api/wirkung/refinements', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

function unauthTuple(): [null, Response] {
  return [
    null,
    new Response(
      JSON.stringify({ error: { code: 'AUTH_REQUIRED', message: 'Authentication required' } }),
      { status: 401 },
    ),
  ];
}

beforeEach(() => {
  vi.clearAllMocks();
  mockDecideRefinement.mockReturnValue(STUB_RECORD);
  mockListRefinements.mockReturnValue([STUB_RECORD]);
  mockFindOrCreateUser.mockReturnValue({ id: 'db-u', email: 'admin@co.com', name: 'Admin' });
});

describe('GET /api/wirkung/refinements — viewer access', () => {
  it('returns 200 with proposal list for an authenticated viewer', async () => {
    mockRequireRole.mockResolvedValue([NORMAL_USER, null]);
    const res = await GET();
    expect(res.status).toBe(200);
    const body = await res.json() as { proposals: unknown[] };
    expect(Array.isArray(body.proposals)).toBe(true);
  });
});

describe('POST /api/wirkung/refinements — admin guard', () => {
  it('returns 401 when not authenticated', async () => {
    mockRequireAuth.mockResolvedValue(unauthTuple());
    const res = await POST(makePostRequest({ proposalKey: 'k', action: 'approve' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when a non-admin attempts approve', async () => {
    mockRequireAuth.mockResolvedValue([NORMAL_USER, null]);
    mockCheckAccess.mockReturnValue(null);
    const res = await POST(makePostRequest({ proposalKey: 'k', action: 'approve' }));
    expect(res.status).toBe(403);
  });

  it('returns 403 when a non-admin attempts reject', async () => {
    mockRequireAuth.mockResolvedValue([NORMAL_USER, null]);
    mockCheckAccess.mockReturnValue(null);
    const res = await POST(makePostRequest({ proposalKey: 'k', action: 'reject' }));
    expect(res.status).toBe(403);
  });

  it('returns 200 when an admin approves', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue({ role: 'admin' });
    const res = await POST(makePostRequest({ proposalKey: 'k', action: 'approve' }));
    expect(res.status).toBe(200);
    const body = await res.json() as { proposal: unknown };
    expect(body.proposal).toBeDefined();
  });

  it('returns 200 when an admin rejects', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue({ role: 'admin' });
    const res = await POST(makePostRequest({ proposalKey: 'k', action: 'reject' }));
    expect(res.status).toBe(200);
    const body = await res.json() as { proposal: unknown };
    expect(body.proposal).toBeDefined();
  });
});
