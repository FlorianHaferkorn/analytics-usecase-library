/**
 * Route-level auth guard tests for POST /api/ai-config.
 *
 * Verifies that `reopen` (a governance decision that reverts an approved config to
 * a mutable state) is gated by the same admin RBAC check as `approve`, and that
 * `submit` remains open to any authenticated user to preserve the two-person model.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

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
  getConfigLayer: vi.fn(),
  upsertConfigLayer: vi.fn(),
  transitionConfigLayer: mockTransitionConfigLayer,
  AiConfigGovernanceError: class AiConfigGovernanceError extends Error {},
}));

import { POST } from '@/app/api/ai-config/route';

const ADMIN_USER = { id: 'u-admin', email: 'admin@co.com', name: 'Admin' };
const NORMAL_USER = { id: 'u-normal', email: 'user@co.com', name: 'User' };
const STUB_ROW = { id: 'cfg-1', status: 'approved', layer: 'L1', domain_id: '' };

function makePostRequest(body: Record<string, unknown>): Request {
  return new Request('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

function unauthTuple(): [null, Response] {
  return [
    null,
    new Response(
      JSON.stringify({ error: { code: 'AUTH_REQUIRED', message: 'Authentication required' } }),
      { status: 401 },
    ),
  ];
}

beforeEach(() => {
  vi.clearAllMocks();
  mockTransitionConfigLayer.mockReturnValue(STUB_ROW);
  mockFindOrCreateUser.mockReturnValue({ id: 'db-u', email: 'admin@co.com', name: 'Admin' });
});

describe('POST /api/ai-config — admin guard', () => {
  it('returns 401 when not authenticated', async () => {
    mockRequireAuth.mockResolvedValue(unauthTuple());
    const res = await POST(makePostRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when a non-admin attempts approve', async () => {
    mockRequireAuth.mockResolvedValue([NORMAL_USER, null]);
    mockCheckAccess.mockReturnValue(null);
    const res = await POST(makePostRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('returns 403 when a non-admin attempts reopen', async () => {
    mockRequireAuth.mockResolvedValue([NORMAL_USER, null]);
    mockCheckAccess.mockReturnValue(null);
    const res = await POST(makePostRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('returns 200 when an admin approves', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue({ role: 'admin' });
    const res = await POST(makePostRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(200);
    const body = await res.json() as { layer: unknown };
    expect(body.layer).toBeDefined();
  });

  it('returns 200 when an admin reopens', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue({ role: 'admin' });
    const res = await POST(makePostRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(200);
    const body = await res.json() as { layer: unknown };
    expect(body.layer).toBeDefined();
  });

  it('returns 200 for submit without an admin check (any authenticated user)', async () => {
    mockRequireAuth.mockResolvedValue([NORMAL_USER, null]);
    const res = await POST(makePostRequest({ op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockCheckAccess).not.toHaveBeenCalled();
  });
});
