/**
 * Route-level RBAC guard tests for POST /api/ai-config.
 *
 * Verifies that `approve` and `reopen` are admin-only operations while
 * `submit` (and other authenticated ops) are available to any signed-in user.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

/* ------------------------------------------------------------------ */
/* Hoisted mocks — must live before any vi.mock() factory              */
/* ------------------------------------------------------------------ */
const { mockRequireAuth, mockCheckAccess } = vi.hoisted(() => {
  const mockRequireAuth = vi.fn();
  const mockCheckAccess = vi.fn();
  return { mockRequireAuth, mockCheckAccess };
});

vi.mock('@/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));
vi.mock('@/lib/db/rbac-repo', () => ({ checkAccess: mockCheckAccess }));
vi.mock('@/lib/db/user-repo', () => ({ findOrCreateUser: vi.fn(() => ({ id: 'u1' })) }));
vi.mock('@/lib/db/ai-config-repo', () => ({
  getConfigLayer: vi.fn(() => ({ status: 'draft' })),
  upsertConfigLayer: vi.fn(() => ({ status: 'draft' })),
  transitionConfigLayer: vi.fn(() => ({ status: 'submitted' })),
  AiConfigGovernanceError: class AiConfigGovernanceError extends Error {},
}));
vi.mock('@/lib/api/response', () => ({
  apiSuccess: vi.fn((data: unknown) =>
    new Response(JSON.stringify(data), { status: 200 })
  ),
  apiError: vi.fn((_code: string, msg: string, status: number) =>
    new Response(JSON.stringify({ error: msg }), { status })
  ),
  apiValidationError: vi.fn((errs: string[]) =>
    new Response(JSON.stringify({ errors: errs }), { status: 422 })
  ),
}));

function makeRequest(body: object): Request {
  return new Request('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

describe('POST /api/ai-config — RBAC guard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns 401 for unauthenticated requests', async () => {
    mockRequireAuth.mockResolvedValue([
      null,
      new Response('Unauthorized', { status: 401 }),
    ]);
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 for non-admin attempting approve', async () => {
    mockRequireAuth.mockResolvedValue([
      { email: 'user@test.com', name: 'User' },
      null,
    ]);
    mockCheckAccess.mockReturnValue(false);
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('returns 403 for non-admin attempting reopen', async () => {
    mockRequireAuth.mockResolvedValue([
      { email: 'user@test.com', name: 'User' },
      null,
    ]);
    mockCheckAccess.mockReturnValue(false);
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('allows admin to approve', async () => {
    mockRequireAuth.mockResolvedValue([
      { email: 'admin@test.com', name: 'Admin' },
      null,
    ]);
    mockCheckAccess.mockReturnValue(true);
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(200);
  });

  it('allows admin to reopen', async () => {
    mockRequireAuth.mockResolvedValue([
      { email: 'admin@test.com', name: 'Admin' },
      null,
    ]);
    mockCheckAccess.mockReturnValue(true);
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(200);
  });

  it('allows non-admin to submit', async () => {
    mockRequireAuth.mockResolvedValue([
      { email: 'user@test.com', name: 'User' },
      null,
    ]);
    // checkAccess is NOT called for submit; mockReturnValue(false) would still let submit through
    mockCheckAccess.mockReturnValue(false);
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeRequest({ op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(200);
  });
});
