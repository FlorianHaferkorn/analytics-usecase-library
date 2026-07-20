/**
 * Route-level guard tests for POST /api/wirkung/refinements.
 * Verifies that `approve` and `reject` require admin RBAC, while GET requires only viewer.
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

const ADMIN_USER = { id: 'usr-admin', email: 'admin@co.com', name: 'Admin' };
const NON_ADMIN_USER = { id: 'usr-editor', email: 'editor@co.com', name: 'Editor' };
const DB_USER = { id: 'usr-001', email: 'admin@co.com', name: 'Admin' };

async function callPost(body: Record<string, unknown>) {
  const { POST } = await import('@/app/api/wirkung/refinements/route');
  return POST(new Request('http://localhost/api/wirkung/refinements', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }));
}

async function callGet() {
  const { GET } = await import('@/app/api/wirkung/refinements/route');
  return GET();
}

describe('POST /api/wirkung/refinements — route guard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
    mockFindOrCreateUser.mockReturnValue(DB_USER);
    mockDecideRefinement.mockReturnValue({ proposal_key: 'key-1', status: 'approved' });
    mockListRefinements.mockReturnValue([]);
  });

  it('returns 401 when not authenticated', async () => {
    mockRequireAuth.mockResolvedValue([null, new Response('Unauthorized', { status: 401 })]);
    const res = await callPost({ proposalKey: 'key-1', action: 'approve' });
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin attempts approve', async () => {
    mockRequireAuth.mockResolvedValue([NON_ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(null);
    const res = await callPost({ proposalKey: 'key-1', action: 'approve', justification: 'ok' });
    expect(res.status).toBe(403);
  });

  it('returns 403 when non-admin attempts reject', async () => {
    mockRequireAuth.mockResolvedValue([NON_ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(null);
    const res = await callPost({ proposalKey: 'key-1', action: 'reject', justification: 'not valid' });
    expect(res.status).toBe(403);
  });

  it('returns 200 when admin approves', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue({ role: 'admin' });
    const res = await callPost({ proposalKey: 'key-1', action: 'approve', justification: 'lgtm' });
    expect(res.status).toBe(200);
    expect(mockDecideRefinement).toHaveBeenCalledWith('key-1', 'approve', ADMIN_USER.email, 'lgtm');
  });

  it('returns 200 when admin rejects', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue({ role: 'admin' });
    const res = await callPost({ proposalKey: 'key-1', action: 'reject', justification: 'out of scope' });
    expect(res.status).toBe(200);
    expect(mockDecideRefinement).toHaveBeenCalledWith('key-1', 'reject', ADMIN_USER.email, 'out of scope');
  });

  it('GET returns 200 with viewer role', async () => {
    mockRequireRole.mockResolvedValue([NON_ADMIN_USER, null]);
    const res = await callGet();
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json).toHaveProperty('proposals');
  });
});
