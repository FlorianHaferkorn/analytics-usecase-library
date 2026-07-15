/**
 * Route-level guard tests for POST /api/ai-config.
 *
 * Critical: both `approve` AND `reopen` require admin RBAC.
 * `submit` is allowed by any authenticated user.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

/* ------------------------------------------------------------------ */
/* Hoisted mocks (must come before module imports)                      */
/* ------------------------------------------------------------------ */

const mockRequireAuth = vi.hoisted(() => vi.fn());
const mockCheckAccess = vi.hoisted(() => vi.fn());
const mockFindOrCreateUser = vi.hoisted(() => vi.fn());
const mockGetConfigLayer = vi.hoisted(() => vi.fn());
const mockUpsertConfigLayer = vi.hoisted(() => vi.fn());
const mockTransitionConfigLayer = vi.hoisted(() => vi.fn());

vi.mock('../../src/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));
vi.mock('../../src/lib/db/rbac-repo', () => ({ checkAccess: mockCheckAccess }));
vi.mock('../../src/lib/db/user-repo', () => ({ findOrCreateUser: mockFindOrCreateUser }));
vi.mock('../../src/lib/db/ai-config-repo', () => ({
  getConfigLayer: mockGetConfigLayer,
  upsertConfigLayer: mockUpsertConfigLayer,
  transitionConfigLayer: mockTransitionConfigLayer,
  AiConfigGovernanceError: class AiConfigGovernanceError extends Error {},
}));

import { POST } from '../../src/app/api/ai-config/route';

/* ------------------------------------------------------------------ */
/* Helpers                                                              */
/* ------------------------------------------------------------------ */

const ADMIN_USER = { email: 'admin@co.com', name: 'Admin' };
const REGULAR_USER = { email: 'user@co.com', name: 'User' };
const ADMIN_DB = { id: 'u-admin', email: 'admin@co.com', name: 'Admin' };
const REGULAR_DB = { id: 'u-reg', email: 'user@co.com', name: 'User' };

function makeRequest(body: Record<string, unknown>): Request {
  return new Request('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

/* ------------------------------------------------------------------ */
/* Tests                                                                */
/* ------------------------------------------------------------------ */

describe('POST /api/ai-config — auth and RBAC guards', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTransitionConfigLayer.mockReturnValue({ id: 'row-1', status: 'approved' });
  });

  it('returns 401 when unauthenticated', async () => {
    mockRequireAuth.mockResolvedValue([null, new Response('Unauthorized', { status: 401 })]);

    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin attempts approve', async () => {
    mockRequireAuth.mockResolvedValue([REGULAR_USER, null]);
    mockFindOrCreateUser.mockReturnValue(REGULAR_DB);
    mockCheckAccess.mockReturnValue(false);

    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
    const body = await res.json();
    expect(body.error.code).toBeDefined();
  });

  it('returns 403 when non-admin attempts reopen', async () => {
    mockRequireAuth.mockResolvedValue([REGULAR_USER, null]);
    mockFindOrCreateUser.mockReturnValue(REGULAR_DB);
    mockCheckAccess.mockReturnValue(false);

    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
    const body = await res.json();
    expect(body.error.code).toBeDefined();
  });

  it('returns 200 when admin approves', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockFindOrCreateUser.mockReturnValue(ADMIN_DB);
    mockCheckAccess.mockReturnValue(true);

    const res = await POST(makeRequest({ op: 'approve', layer: 'L1', justification: 'Approved' }));
    expect(res.status).toBe(200);
  });

  it('returns 200 when admin reopens', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockFindOrCreateUser.mockReturnValue(ADMIN_DB);
    mockCheckAccess.mockReturnValue(true);

    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1', justification: 'Re-opening for revision' }));
    expect(res.status).toBe(200);
  });

  it('returns 200 when any authenticated user submits (no admin check)', async () => {
    mockRequireAuth.mockResolvedValue([REGULAR_USER, null]);

    const res = await POST(makeRequest({ op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockCheckAccess).not.toHaveBeenCalled();
  });
});
