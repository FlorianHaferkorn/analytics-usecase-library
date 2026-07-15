/**
 * Route-level guard tests for GET/POST /api/wirkung/refinements.
 *
 * Critical: both `approve` AND `reject` require admin RBAC.
 * GET (list) requires only viewer role.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

/* ------------------------------------------------------------------ */
/* Hoisted mocks (must come before module imports)                      */
/* ------------------------------------------------------------------ */

const mockRequireAuth = vi.hoisted(() => vi.fn());
const mockRequireRole = vi.hoisted(() => vi.fn());
const mockCheckAccess = vi.hoisted(() => vi.fn());
const mockFindOrCreateUser = vi.hoisted(() => vi.fn());
const mockDecideRefinement = vi.hoisted(() => vi.fn());
const mockListRefinements = vi.hoisted(() => vi.fn());

vi.mock('../../src/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));
vi.mock('../../src/lib/auth/require-role', () => ({ requireRole: mockRequireRole }));
vi.mock('../../src/lib/db/rbac-repo', () => ({ checkAccess: mockCheckAccess }));
vi.mock('../../src/lib/db/user-repo', () => ({ findOrCreateUser: mockFindOrCreateUser }));
vi.mock('../../src/lib/governance/refinement-workflow', () => ({
  decideRefinement: mockDecideRefinement,
  listRefinements: mockListRefinements,
}));

import { GET, POST } from '../../src/app/api/wirkung/refinements/route';

/* ------------------------------------------------------------------ */
/* Helpers                                                              */
/* ------------------------------------------------------------------ */

const ADMIN_USER = { email: 'admin@co.com', name: 'Admin' };
const REGULAR_USER = { email: 'user@co.com', name: 'User' };
const ADMIN_DB = { id: 'u-admin', email: 'admin@co.com', name: 'Admin' };
const REGULAR_DB = { id: 'u-reg', email: 'user@co.com', name: 'User' };

function makePostRequest(body: Record<string, unknown>): Request {
  return new Request('http://localhost/api/wirkung/refinements', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

/* ------------------------------------------------------------------ */
/* Tests                                                                */
/* ------------------------------------------------------------------ */

describe('POST /api/wirkung/refinements — auth and RBAC guards', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockDecideRefinement.mockReturnValue({ proposalKey: 'k1', decision: 'approved' });
  });

  it('returns 401 when unauthenticated', async () => {
    mockRequireAuth.mockResolvedValue([null, new Response('Unauthorized', { status: 401 })]);

    const res = await POST(makePostRequest({ proposalKey: 'k1', action: 'approve' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin attempts approve', async () => {
    mockRequireAuth.mockResolvedValue([REGULAR_USER, null]);
    mockFindOrCreateUser.mockReturnValue(REGULAR_DB);
    mockCheckAccess.mockReturnValue(false);

    const res = await POST(makePostRequest({ proposalKey: 'k1', action: 'approve' }));
    expect(res.status).toBe(403);
    const body = await res.json();
    expect(body.error.code).toBeDefined();
  });

  it('returns 403 when non-admin attempts reject', async () => {
    mockRequireAuth.mockResolvedValue([REGULAR_USER, null]);
    mockFindOrCreateUser.mockReturnValue(REGULAR_DB);
    mockCheckAccess.mockReturnValue(false);

    const res = await POST(makePostRequest({ proposalKey: 'k1', action: 'reject' }));
    expect(res.status).toBe(403);
    const body = await res.json();
    expect(body.error.code).toBeDefined();
  });

  it('returns 200 when admin approves', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockFindOrCreateUser.mockReturnValue(ADMIN_DB);
    mockCheckAccess.mockReturnValue(true);

    const res = await POST(makePostRequest({ proposalKey: 'k1', action: 'approve', justification: 'Approved' }));
    expect(res.status).toBe(200);
  });

  it('returns 200 when admin rejects', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockFindOrCreateUser.mockReturnValue(ADMIN_DB);
    mockCheckAccess.mockReturnValue(true);

    const res = await POST(makePostRequest({ proposalKey: 'k1', action: 'reject', justification: 'Not suitable' }));
    expect(res.status).toBe(200);
  });
});

describe('GET /api/wirkung/refinements — viewer access', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListRefinements.mockReturnValue([]);
  });

  it('returns 200 with proposals list when viewer authenticated', async () => {
    mockRequireRole.mockResolvedValue([{ email: 'viewer@co.com' }, null]);

    const res = await GET();
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(Array.isArray(body.proposals)).toBe(true);
  });
});
