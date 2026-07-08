/**
 * Route-level guard tests for the AI-config governance API.
 * Specifically validates that both `approve` AND `reopen` require admin RBAC,
 * while `submit` is available to any authenticated user.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { SessionUser } from '@/lib/auth/session';

/* ------------------------------------------------------------------ */
/* vi.hoisted — mock factories referenced inside vi.mock() closures   */
/* ------------------------------------------------------------------ */

const { mockRequireAuth, mockCheckAccess, mockFindOrCreateUser, mockTransition, mockUpsert, mockGetLayer } = vi.hoisted(() => {
  return {
    mockRequireAuth:      vi.fn(),
    mockCheckAccess:      vi.fn(),
    mockFindOrCreateUser: vi.fn(),
    mockTransition:       vi.fn(),
    mockUpsert:           vi.fn(),
    mockGetLayer:         vi.fn(),
  };
});

vi.mock('@/lib/auth/session',      () => ({ requireAuth: mockRequireAuth }));
vi.mock('@/lib/db/rbac-repo',      () => ({ checkAccess: mockCheckAccess }));
vi.mock('@/lib/db/user-repo',      () => ({ findOrCreateUser: mockFindOrCreateUser }));
vi.mock('@/lib/db/ai-config-repo', () => ({
  getConfigLayer:         mockGetLayer,
  upsertConfigLayer:      mockUpsert,
  transitionConfigLayer:  mockTransition,
  AiConfigGovernanceError: class AiConfigGovernanceError extends Error {},
}));

/* ------------------------------------------------------------------ */
/* Helpers                                                              */
/* ------------------------------------------------------------------ */

const ADMIN_USER: SessionUser   = { id: 'u-admin',  email: 'admin@co.com',  name: 'Admin'  };
const EDITOR_USER: SessionUser  = { id: 'u-editor', email: 'editor@co.com', name: 'Editor' };
const FAKE_ROW = { id: 'row-1', status: 'approved' };

function makeRequest(body: Record<string, unknown>): Request {
  return new Request('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });
}

/* ------------------------------------------------------------------ */
/* Tests                                                                */
/* ------------------------------------------------------------------ */

describe('POST /api/ai-config — route guard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTransition.mockReturnValue(FAKE_ROW);
    mockFindOrCreateUser.mockReturnValue({ id: 'u-admin', email: 'admin@co.com', name: 'Admin' });
  });

  it('returns 401 when unauthenticated', async () => {
    mockRequireAuth.mockResolvedValue([null, new Response('Unauthorized', { status: 401 })]);
    const { POST } = await import('../../src/app/api/ai-config/route');

    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when a non-admin attempts approve', async () => {
    mockRequireAuth.mockResolvedValue([EDITOR_USER, null]);
    mockFindOrCreateUser.mockReturnValue({ id: 'u-editor' });
    mockCheckAccess.mockReturnValue(undefined); // not admin
    const { POST } = await import('../../src/app/api/ai-config/route');

    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
    expect(mockTransition).not.toHaveBeenCalled();
  });

  it('returns 403 when a non-admin attempts reopen', async () => {
    mockRequireAuth.mockResolvedValue([EDITOR_USER, null]);
    mockFindOrCreateUser.mockReturnValue({ id: 'u-editor' });
    mockCheckAccess.mockReturnValue(undefined); // not admin
    const { POST } = await import('../../src/app/api/ai-config/route');

    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
    expect(mockTransition).not.toHaveBeenCalled();
  });

  it('returns 200 when an admin approves', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue({ id: 'u-admin', role: 'admin' });
    const { POST } = await import('../../src/app/api/ai-config/route');

    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockTransition).toHaveBeenCalledWith('default', 'L1', '', 'approve', ADMIN_USER.email, '');
  });

  it('returns 200 when an admin reopens', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue({ id: 'u-admin', role: 'admin' });
    const { POST } = await import('../../src/app/api/ai-config/route');

    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockTransition).toHaveBeenCalledWith('default', 'L1', '', 'reopen', ADMIN_USER.email, '');
  });

  it('returns 200 when any authenticated user submits (no admin gate)', async () => {
    mockRequireAuth.mockResolvedValue([EDITOR_USER, null]);
    const { POST } = await import('../../src/app/api/ai-config/route');

    const res = await POST(makeRequest({ op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockCheckAccess).not.toHaveBeenCalled();
    expect(mockTransition).toHaveBeenCalledWith('default', 'L1', '', 'submit', EDITOR_USER.email, '');
  });
});
