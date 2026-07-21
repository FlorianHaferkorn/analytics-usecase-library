/**
 * Route-level auth guard tests for POST /api/wirkung/refinements
 * Verifies that `approve` AND `reject` require admin RBAC, while GET (viewer) does not.
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

beforeEach(() => {
  vi.clearAllMocks();
});

async function callPost(body: Record<string, unknown>) {
  const { POST } = await import('@/app/api/wirkung/refinements/route');
  const req = new Request('http://localhost/api/wirkung/refinements', {
    method: 'POST',
    body: JSON.stringify(body),
  });
  return POST(req);
}

async function callGet() {
  const { GET } = await import('@/app/api/wirkung/refinements/route');
  return GET();
}

describe('POST /api/wirkung/refinements — auth guards', () => {
  it('returns 401 when not authenticated', async () => {
    mockRequireAuth.mockResolvedValueOnce([null, new Response('Unauthorized', { status: 401 })]);
    const res = await callPost({ proposalKey: 'k1', action: 'approve' });
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin attempts approve', async () => {
    mockRequireAuth.mockResolvedValueOnce([{ email: 'alice@example.com', name: 'Alice' }, null]);
    mockFindOrCreateUser.mockReturnValueOnce({ id: 'usr-alice' });
    mockCheckAccess.mockReturnValueOnce(false);
    const res = await callPost({ proposalKey: 'k1', action: 'approve' });
    expect(res.status).toBe(403);
  });

  it('returns 403 when non-admin attempts reject', async () => {
    mockRequireAuth.mockResolvedValueOnce([{ email: 'alice@example.com', name: 'Alice' }, null]);
    mockFindOrCreateUser.mockReturnValueOnce({ id: 'usr-alice' });
    mockCheckAccess.mockReturnValueOnce(false);
    const res = await callPost({ proposalKey: 'k1', action: 'reject' });
    expect(res.status).toBe(403);
  });

  it('returns 200 when admin approves', async () => {
    mockRequireAuth.mockResolvedValueOnce([{ email: 'admin@example.com', name: 'Admin' }, null]);
    mockFindOrCreateUser.mockReturnValueOnce({ id: 'usr-admin' });
    mockCheckAccess.mockReturnValueOnce(true);
    mockDecideRefinement.mockReturnValueOnce({ proposalKey: 'k1', decision: 'approve' });
    const res = await callPost({ proposalKey: 'k1', action: 'approve', justification: 'ok' });
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.proposal.decision).toBe('approve');
  });

  it('returns 200 when admin rejects', async () => {
    mockRequireAuth.mockResolvedValueOnce([{ email: 'admin@example.com', name: 'Admin' }, null]);
    mockFindOrCreateUser.mockReturnValueOnce({ id: 'usr-admin' });
    mockCheckAccess.mockReturnValueOnce(true);
    mockDecideRefinement.mockReturnValueOnce({ proposalKey: 'k1', decision: 'reject' });
    const res = await callPost({ proposalKey: 'k1', action: 'reject', justification: 'not ready' });
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.proposal.decision).toBe('reject');
  });

  it('GET returns proposals for viewer role without admin check', async () => {
    mockRequireRole.mockResolvedValueOnce([{ email: 'viewer@example.com', name: 'Viewer' }, null]);
    mockListRefinements.mockReturnValueOnce([{ proposalKey: 'k1', status: 'pending' }]);
    const res = await callGet();
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.proposals).toHaveLength(1);
    expect(mockCheckAccess).not.toHaveBeenCalled();
  });
});
