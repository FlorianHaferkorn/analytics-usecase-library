/**
 * Route-level RBAC guard tests for /api/ai-config.
 *
 * Verifies that `approve` AND `reopen` are both admin-gated, while `submit`
 * is accessible to any authenticated user.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

// vi.hoisted() ensures the factory refs are available when vi.mock() hoists the
// mock call to the top of the file (before any imports are evaluated).
const { mockRequireAuth, mockCheckAccess, mockFindOrCreateUser, mockTransition, mockGetConfig } =
  vi.hoisted(() => ({
    mockRequireAuth: vi.fn(),
    mockCheckAccess: vi.fn(),
    mockFindOrCreateUser: vi.fn(),
    mockTransition: vi.fn(),
    mockGetConfig: vi.fn(),
  }));

vi.mock('@/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));
vi.mock('@/lib/db/rbac-repo', () => ({ checkAccess: mockCheckAccess }));
vi.mock('@/lib/db/user-repo', () => ({ findOrCreateUser: mockFindOrCreateUser }));
vi.mock('@/lib/db/ai-config-repo', () => ({
  getConfigLayer: mockGetConfig,
  upsertConfigLayer: vi.fn(),
  transitionConfigLayer: mockTransition,
  AiConfigGovernanceError: class AiConfigGovernanceError extends Error {},
}));

function makeRequest(body: object): Request {
  return new Request('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });
}

const ADMIN_USER = { email: 'admin@co.com', name: 'Admin' };
const REGULAR_USER = { email: 'user@co.com', name: 'User' };
const FAKE_ROW = { id: 'r1', status: 'approved' };

describe('POST /api/ai-config — RBAC guards', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('returns 401 when the request is not authenticated', async () => {
    const fakeAuthError = new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
    mockRequireAuth.mockResolvedValueOnce([null, fakeAuthError]);

    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when a non-admin tries to approve', async () => {
    mockRequireAuth.mockResolvedValueOnce([REGULAR_USER, null]);
    mockFindOrCreateUser.mockReturnValueOnce({ id: 'u2' });
    mockCheckAccess.mockReturnValueOnce(false);

    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('returns 403 when a non-admin tries to reopen', async () => {
    mockRequireAuth.mockResolvedValueOnce([REGULAR_USER, null]);
    mockFindOrCreateUser.mockReturnValueOnce({ id: 'u2' });
    mockCheckAccess.mockReturnValueOnce(false);

    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('allows an admin to approve', async () => {
    mockRequireAuth.mockResolvedValueOnce([ADMIN_USER, null]);
    mockFindOrCreateUser.mockReturnValueOnce({ id: 'u1' });
    mockCheckAccess.mockReturnValueOnce(true);
    mockTransition.mockReturnValueOnce(FAKE_ROW);

    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(200);
    const body = await res.json() as { layer: unknown };
    expect(body.layer).toEqual(FAKE_ROW);
  });

  it('allows an admin to reopen', async () => {
    mockRequireAuth.mockResolvedValueOnce([ADMIN_USER, null]);
    mockFindOrCreateUser.mockReturnValueOnce({ id: 'u1' });
    mockCheckAccess.mockReturnValueOnce(true);
    mockTransition.mockReturnValueOnce(FAKE_ROW);

    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(200);
    const body = await res.json() as { layer: unknown };
    expect(body.layer).toEqual(FAKE_ROW);
  });

  it('allows any authenticated user to submit (no admin required)', async () => {
    mockRequireAuth.mockResolvedValueOnce([REGULAR_USER, null]);
    mockTransition.mockReturnValueOnce(FAKE_ROW);

    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeRequest({ op: 'submit', layer: 'L1' }));
    // checkAccess must NOT have been called — submit is not admin-gated.
    expect(mockCheckAccess).not.toHaveBeenCalled();
    expect(res.status).toBe(200);
  });
});
