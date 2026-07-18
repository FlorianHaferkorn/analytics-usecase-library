/**
 * Route-level guard tests for POST /api/ai-config.
 *
 * Verifies that:
 *  - unauthenticated requests receive 401
 *  - non-admin callers are blocked from `approve` AND `reopen` (403)
 *  - admin callers may `approve` and `reopen` (200)
 *  - any authenticated user may `submit` (200)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

const mockRequireAuth = vi.hoisted(() => vi.fn());
const mockCheckAccess = vi.hoisted(() => vi.fn());
const mockFindOrCreateUser = vi.hoisted(() => vi.fn());
const mockTransitionConfigLayer = vi.hoisted(() => vi.fn());
const mockGetConfigLayer = vi.hoisted(() => vi.fn());
const mockUpsertConfigLayer = vi.hoisted(() => vi.fn());

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

const AUTHED_USER = { email: 'user@test.local', name: 'User' };
const UNAUTHED = [null, new Response('Unauthorized', { status: 401 })] as const;
const AUTHED = [AUTHED_USER, null] as const;
const DB_USER = { id: 'user-1' };

function makeRequest(body: object): Request {
  return new Request('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  mockFindOrCreateUser.mockReturnValue(DB_USER);
  mockTransitionConfigLayer.mockReturnValue({ status: 'approved' });
});

describe('POST /api/ai-config — RBAC guard', () => {
  it('returns 401 when not authenticated', async () => {
    mockRequireAuth.mockResolvedValue(UNAUTHED);
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin tries to approve', async () => {
    mockRequireAuth.mockResolvedValue(AUTHED);
    mockCheckAccess.mockReturnValue(null); // not admin
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('returns 403 when non-admin tries to reopen (regression guard)', async () => {
    mockRequireAuth.mockResolvedValue(AUTHED);
    mockCheckAccess.mockReturnValue(null); // not admin
    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('returns 200 when admin approves', async () => {
    mockRequireAuth.mockResolvedValue(AUTHED);
    mockCheckAccess.mockReturnValue({ role: 'admin' }); // admin
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1', justification: 'ok' }));
    expect(res.status).toBe(200);
  });

  it('returns 200 when admin reopens', async () => {
    mockRequireAuth.mockResolvedValue(AUTHED);
    mockCheckAccess.mockReturnValue({ role: 'admin' }); // admin
    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1', justification: 'fix' }));
    expect(res.status).toBe(200);
  });

  it('returns 200 when authenticated non-admin submits', async () => {
    mockRequireAuth.mockResolvedValue(AUTHED);
    // checkAccess should NOT be called for submit — verify it is not reached
    const res = await POST(makeRequest({ op: 'submit', layer: 'L1', justification: 'propose' }));
    expect(res.status).toBe(200);
    expect(mockCheckAccess).not.toHaveBeenCalled();
  });
});
