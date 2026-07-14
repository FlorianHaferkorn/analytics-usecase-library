/**
 * Route-level guard tests for POST /api/ai-config.
 *
 * Verifies that `approve` and `reopen` (both governance-mutating operations)
 * require admin RBAC, while `submit` does not.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

const { mockRequireAuth, mockCheckAccess, mockFindOrCreateUser, mockTransitionConfig } = vi.hoisted(() => ({
  mockRequireAuth: vi.fn(),
  mockCheckAccess: vi.fn(),
  mockFindOrCreateUser: vi.fn(),
  mockTransitionConfig: vi.fn(),
}));

vi.mock('@/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));
vi.mock('@/lib/db/rbac-repo', () => ({ checkAccess: mockCheckAccess }));
vi.mock('@/lib/db/user-repo', () => ({ findOrCreateUser: mockFindOrCreateUser }));
vi.mock('@/lib/db/ai-config-repo', () => ({
  getConfigLayer: vi.fn(),
  upsertConfigLayer: vi.fn(),
  transitionConfigLayer: mockTransitionConfig,
  AiConfigGovernanceError: class AiConfigGovernanceError extends Error {},
}));

import { POST } from '../../src/app/api/ai-config/route';

const ADMIN_USER = { id: 'u1', email: 'admin@co.com', name: 'Admin' };
const NON_ADMIN_USER = { id: 'u2', email: 'user@co.com', name: 'User' };
const DB_USER = { id: 42 };
const LAYER_ROW = { id: 'row1', status: 'approved' };

function buildRequest(body: Record<string, unknown>): Request {
  return new Request('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  mockFindOrCreateUser.mockReturnValue(DB_USER);
  mockTransitionConfig.mockReturnValue(LAYER_ROW);
});

describe('POST /api/ai-config — auth guard', () => {
  it('returns 401 when unauthenticated', async () => {
    mockRequireAuth.mockResolvedValue([null, new Response('', { status: 401 })]);

    const res = await POST(buildRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin tries to approve', async () => {
    mockRequireAuth.mockResolvedValue([NON_ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(false);

    const res = await POST(buildRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
    expect(mockCheckAccess).toHaveBeenCalledWith('default', DB_USER.id, 'admin');
  });

  it('returns 403 when non-admin tries to reopen', async () => {
    mockRequireAuth.mockResolvedValue([NON_ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(false);

    const res = await POST(buildRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
    expect(mockCheckAccess).toHaveBeenCalledWith('default', DB_USER.id, 'admin');
  });

  it('succeeds (200) when admin approves', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(true);

    const res = await POST(buildRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(200);
    const body = await res.json() as { layer: unknown };
    expect(body.layer).toEqual(LAYER_ROW);
  });

  it('succeeds (200) when admin reopens', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(true);

    const res = await POST(buildRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(200);
    const body = await res.json() as { layer: unknown };
    expect(body.layer).toEqual(LAYER_ROW);
  });

  it('succeeds (200) when non-admin submits (no admin check needed)', async () => {
    mockRequireAuth.mockResolvedValue([NON_ADMIN_USER, null]);

    const res = await POST(buildRequest({ op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockCheckAccess).not.toHaveBeenCalled();
  });
});
