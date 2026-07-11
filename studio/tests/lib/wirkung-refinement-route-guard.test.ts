/**
 * Route-level RBAC guard tests for POST /api/wirkung/refinements.
 *
 * Ensures:
 *  - Unauthenticated requests → 401
 *  - Non-admin `approve` → 403
 *  - Non-admin `reject` → 403  (regression: was missing before this fix)
 *  - Admin `approve` → 200
 *  - Admin `reject` → 200
 *  - GET (viewer) → 200  (read-only, no mutation)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

const { mockRequireAuth, mockRequireRole, mockCheckAccess, mockFindOrCreateUser, mockDecide, mockList } = vi.hoisted(() => ({
  mockRequireAuth: vi.fn(),
  mockRequireRole: vi.fn(),
  mockCheckAccess: vi.fn(),
  mockFindOrCreateUser: vi.fn(),
  mockDecide: vi.fn(),
  mockList: vi.fn(),
}));

vi.mock('@/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: mockRequireRole }));
vi.mock('@/lib/db/rbac-repo', () => ({ checkAccess: mockCheckAccess }));
vi.mock('@/lib/db/user-repo', () => ({ findOrCreateUser: mockFindOrCreateUser }));
vi.mock('@/lib/governance/refinement-workflow', () => ({
  decideRefinement: mockDecide,
  listRefinements: mockList,
}));

const ADMIN_USER = { email: 'admin@example.com', name: 'Admin' };
const VIEWER_USER = { email: 'viewer@example.com', name: 'Viewer' };
const DB_USER = { id: 'u1', email: 'admin@example.com' };
const STUB_PROPOSAL = { proposal_key: 'ac1::kpi1', status: 'approved' };

function makePostReq(body: Record<string, unknown>): Request {
  return new Request('http://localhost/api/wirkung/refinements', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  });
}

function makeGetReq(): Request {
  return new Request('http://localhost/api/wirkung/refinements', { method: 'GET' });
}

beforeEach(() => {
  vi.clearAllMocks();
  mockDecide.mockReturnValue(STUB_PROPOSAL);
  mockList.mockReturnValue([STUB_PROPOSAL]);
  mockFindOrCreateUser.mockReturnValue(DB_USER);
});

describe('POST /api/wirkung/refinements — RBAC guard', () => {
  it('returns 401 when not authenticated', async () => {
    mockRequireAuth.mockResolvedValue([null, new Response('Unauthorized', { status: 401 })]);
    const { POST } = await import('@/app/api/wirkung/refinements/route');
    const res = await POST(makePostReq({ proposalKey: 'ac1::kpi1', action: 'approve' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin attempts approve', async () => {
    mockRequireAuth.mockResolvedValue([VIEWER_USER, null]);
    mockCheckAccess.mockReturnValue(false);
    const { POST } = await import('@/app/api/wirkung/refinements/route');
    const res = await POST(makePostReq({ proposalKey: 'ac1::kpi1', action: 'approve' }));
    expect(res.status).toBe(403);
  });

  it('returns 403 when non-admin attempts reject', async () => {
    mockRequireAuth.mockResolvedValue([VIEWER_USER, null]);
    mockCheckAccess.mockReturnValue(false);
    const { POST } = await import('@/app/api/wirkung/refinements/route');
    const res = await POST(makePostReq({ proposalKey: 'ac1::kpi1', action: 'reject' }));
    expect(res.status).toBe(403);
  });

  it('allows admin to approve', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(true);
    const { POST } = await import('@/app/api/wirkung/refinements/route');
    const res = await POST(makePostReq({ proposalKey: 'ac1::kpi1', action: 'approve' }));
    expect(res.status).toBe(200);
  });

  it('allows admin to reject', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(true);
    const { POST } = await import('@/app/api/wirkung/refinements/route');
    const res = await POST(makePostReq({ proposalKey: 'ac1::kpi1', action: 'reject' }));
    expect(res.status).toBe(200);
  });
});

describe('GET /api/wirkung/refinements — viewer read access', () => {
  it('returns 200 for an authenticated viewer', async () => {
    mockRequireRole.mockResolvedValue([VIEWER_USER, null]);
    const { GET } = await import('@/app/api/wirkung/refinements/route');
    const res = await GET();
    expect(res.status).toBe(200);
  });
});
