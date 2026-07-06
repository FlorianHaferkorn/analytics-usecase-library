/**
 * Route-level RBAC guard tests for /api/ai-config.
 *
 * Verifies that `approve` AND `reopen` both require admin, while `submit` does not.
 * These tests live at the route handler level (HTTP layer), not the repo layer.
 */

import { describe, it, expect, vi } from 'vitest';

/* ------------------------------------------------------------------ */
/* Hoisted mocks (must precede vi.mock factories)                       */
/* ------------------------------------------------------------------ */

const { mockRequireAuth, mockCheckAccess, mockFindOrCreateUser, mockTransitionConfigLayer } =
  vi.hoisted(() => ({
    mockRequireAuth: vi.fn(),
    mockCheckAccess: vi.fn(),
    mockFindOrCreateUser: vi.fn(),
    mockTransitionConfigLayer: vi.fn(),
  }));

vi.mock('@/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));
vi.mock('@/lib/db/rbac-repo', () => ({ checkAccess: mockCheckAccess }));
vi.mock('@/lib/db/user-repo', () => ({ findOrCreateUser: mockFindOrCreateUser }));
vi.mock('@/lib/db/ai-config-repo', () => ({
  getConfigLayer: vi.fn().mockReturnValue(null),
  upsertConfigLayer: vi.fn().mockReturnValue({ status: 'draft' }),
  transitionConfigLayer: mockTransitionConfigLayer,
  AiConfigGovernanceError: class AiConfigGovernanceError extends Error {},
}));

/* ------------------------------------------------------------------ */
/* Helpers                                                               */
/* ------------------------------------------------------------------ */

const ADMIN_USER = { email: 'admin@co.com', name: 'Admin' };
const USER      = { email: 'user@co.com',  name: 'User'  };
const LAYER_ROW = { status: 'submitted', layer: 'L1' };

function makeRequest(body: Record<string, unknown>): Request {
  return new Request('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

/* ------------------------------------------------------------------ */
/* Tests                                                                 */
/* ------------------------------------------------------------------ */

describe('POST /api/ai-config — RBAC guard', () => {
  it('returns 401 when unauthenticated', async () => {
    const { POST } = await import('@/app/api/ai-config/route');
    const unauth = new Response('Unauthorized', { status: 401 });
    mockRequireAuth.mockResolvedValue([null, unauth]);

    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin attempts approve', async () => {
    const { POST } = await import('@/app/api/ai-config/route');
    mockRequireAuth.mockResolvedValue([USER, null]);
    mockFindOrCreateUser.mockReturnValue({ id: 'u1' });
    mockCheckAccess.mockReturnValue(false);

    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('returns 403 when non-admin attempts reopen', async () => {
    const { POST } = await import('@/app/api/ai-config/route');
    mockRequireAuth.mockResolvedValue([USER, null]);
    mockFindOrCreateUser.mockReturnValue({ id: 'u1' });
    mockCheckAccess.mockReturnValue(false);

    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('returns 200 when admin approves', async () => {
    const { POST } = await import('@/app/api/ai-config/route');
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockFindOrCreateUser.mockReturnValue({ id: 'a1' });
    mockCheckAccess.mockReturnValue(true);
    mockTransitionConfigLayer.mockReturnValue(LAYER_ROW);

    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.layer).toEqual(LAYER_ROW);
  });

  it('returns 200 when admin reopens', async () => {
    const { POST } = await import('@/app/api/ai-config/route');
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockFindOrCreateUser.mockReturnValue({ id: 'a1' });
    mockCheckAccess.mockReturnValue(true);
    mockTransitionConfigLayer.mockReturnValue(LAYER_ROW);

    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.layer).toEqual(LAYER_ROW);
  });

  it('returns 200 when non-admin submits (submit is not admin-gated)', async () => {
    const { POST } = await import('@/app/api/ai-config/route');
    mockRequireAuth.mockResolvedValue([USER, null]);
    mockTransitionConfigLayer.mockReturnValue(LAYER_ROW);

    const res = await POST(makeRequest({ op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(200);
  });
});
