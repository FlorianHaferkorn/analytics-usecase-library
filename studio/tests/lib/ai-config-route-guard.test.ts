/**
 * Route-level RBAC guard tests for POST /api/ai-config.
 *
 * Critical: both `approve` AND `reopen` are governance decisions and must require
 * admin. Any other authenticated user (submit, reject) must NOT require admin.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

const mockRequireAuth = vi.hoisted(() => vi.fn());
const mockCheckAccess = vi.hoisted(() => vi.fn());
const mockFindOrCreateUser = vi.hoisted(() => vi.fn());
const mockTransitionConfigLayer = vi.hoisted(() => vi.fn());
const mockUpsertConfigLayer = vi.hoisted(() => vi.fn());
const mockGetConfigLayer = vi.hoisted(() => vi.fn());

vi.mock('@/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));
vi.mock('@/lib/db/rbac-repo', () => ({ checkAccess: mockCheckAccess }));
vi.mock('@/lib/db/user-repo', () => ({ findOrCreateUser: mockFindOrCreateUser }));
vi.mock('@/lib/db/ai-config-repo', () => ({
  getConfigLayer: mockGetConfigLayer,
  upsertConfigLayer: mockUpsertConfigLayer,
  transitionConfigLayer: mockTransitionConfigLayer,
  AiConfigGovernanceError: class AiConfigGovernanceError extends Error {},
}));

import { POST } from '@/app/api/ai-config/route';

const ADMIN_USER = { email: 'admin@co.com', name: 'Admin' };
const NON_ADMIN_USER = { email: 'user@co.com', name: 'User' };

function makeRequest(body: object): Request {
  return new Request('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  mockFindOrCreateUser.mockReturnValue({ id: 'user-1' });
  mockTransitionConfigLayer.mockReturnValue({ status: 'approved' });
});

describe('POST /api/ai-config — RBAC guard', () => {
  it('returns 401 when not authenticated', async () => {
    mockRequireAuth.mockResolvedValue([null, new Response(null, { status: 401 })]);
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin tries to approve', async () => {
    mockRequireAuth.mockResolvedValue([NON_ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(false);
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
    expect(mockTransitionConfigLayer).not.toHaveBeenCalled();
  });

  it('returns 403 when non-admin tries to reopen', async () => {
    mockRequireAuth.mockResolvedValue([NON_ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(false);
    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
    expect(mockTransitionConfigLayer).not.toHaveBeenCalled();
  });

  it('returns 200 when admin approves', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(true);
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockTransitionConfigLayer).toHaveBeenCalledWith('default', 'L1', '', 'approve', ADMIN_USER.email, '');
  });

  it('returns 200 when admin reopens', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(true);
    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockTransitionConfigLayer).toHaveBeenCalledWith('default', 'L1', '', 'reopen', ADMIN_USER.email, '');
  });

  it('allows non-admin to submit (no admin check for submit)', async () => {
    mockRequireAuth.mockResolvedValue([NON_ADMIN_USER, null]);
    const res = await POST(makeRequest({ op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockCheckAccess).not.toHaveBeenCalled();
    expect(mockTransitionConfigLayer).toHaveBeenCalledWith('default', 'L1', '', 'submit', NON_ADMIN_USER.email, '');
  });
});
