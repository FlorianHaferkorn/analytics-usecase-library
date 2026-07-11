/**
 * Route-level RBAC guard tests for /api/ai-config.
 *
 * Ensures:
 *  - Unauthenticated requests → 401
 *  - Non-admin `approve` → 403
 *  - Non-admin `reopen` → 403  (regression: was missing before this fix)
 *  - Admin `approve` → 200
 *  - Admin `reopen` → 200
 *  - Non-admin `submit` → 200  (submit is not admin-gated)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

const { mockRequireAuth, mockCheckAccess, mockFindOrCreateUser, mockTransition, mockGetConfig } = vi.hoisted(() => ({
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

function makeReq(body: Record<string, unknown>): Request {
  return new Request('http://localhost/api/ai-config', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  });
}

const ADMIN_USER = { email: 'admin@example.com', name: 'Admin' };
const VIEWER_USER = { email: 'viewer@example.com', name: 'Viewer' };
const DB_USER = { id: 'u1', email: 'admin@example.com' };

beforeEach(() => {
  vi.clearAllMocks();
  mockTransition.mockReturnValue({ status: 'approved' });
  mockGetConfig.mockReturnValue({ status: 'draft' });
  mockFindOrCreateUser.mockReturnValue(DB_USER);
});

describe('POST /api/ai-config — RBAC guard', () => {
  it('returns 401 when not authenticated', async () => {
    mockRequireAuth.mockResolvedValue([null, new Response('Unauthorized', { status: 401 })]);
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeReq({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin attempts approve', async () => {
    mockRequireAuth.mockResolvedValue([VIEWER_USER, null]);
    mockCheckAccess.mockReturnValue(false);
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeReq({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('returns 403 when non-admin attempts reopen', async () => {
    mockRequireAuth.mockResolvedValue([VIEWER_USER, null]);
    mockCheckAccess.mockReturnValue(false);
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeReq({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('allows admin to approve', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(true);
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeReq({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(200);
  });

  it('allows admin to reopen', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(true);
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeReq({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(200);
  });

  it('allows non-admin to submit (submit is not admin-gated)', async () => {
    mockRequireAuth.mockResolvedValue([VIEWER_USER, null]);
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(makeReq({ op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockCheckAccess).not.toHaveBeenCalled();
  });
});
