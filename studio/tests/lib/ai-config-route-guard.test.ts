/**
 * Route-level guard tests for POST /api/ai-config
 * Verifies that admin RBAC is enforced for both `approve` and `reopen` operations.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockRequireAuth = vi.hoisted(() => vi.fn());
const mockCheckAccess = vi.hoisted(() => vi.fn());
const mockFindOrCreateUser = vi.hoisted(() => vi.fn());
const mockGetConfigLayer = vi.hoisted(() => vi.fn());
const mockUpsertConfigLayer = vi.hoisted(() => vi.fn());
const mockTransitionConfigLayer = vi.hoisted(() => vi.fn());

vi.mock('@/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));
vi.mock('@/lib/db/rbac-repo', () => ({ checkAccess: mockCheckAccess }));
vi.mock('@/lib/db/user-repo', () => ({ findOrCreateUser: mockFindOrCreateUser }));
vi.mock('@/lib/db/ai-config-repo', () => ({
  getConfigLayer: mockGetConfigLayer,
  upsertConfigLayer: mockUpsertConfigLayer,
  transitionConfigLayer: mockTransitionConfigLayer,
  AiConfigGovernanceError: class AiConfigGovernanceError extends Error {},
}));

const { POST } = await import('@/app/api/ai-config/route');

const USER = { email: 'user@test.com', name: 'Test User' };
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
  mockTransitionConfigLayer.mockReturnValue({ id: 'row-1', status: 'approved' });
});

describe('POST /api/ai-config — auth guard', () => {
  it('returns 401 when unauthenticated', async () => {
    const authErr = new Response('Unauthorized', { status: 401 });
    mockRequireAuth.mockResolvedValue([null, authErr]);
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin tries to approve', async () => {
    mockRequireAuth.mockResolvedValue([USER, null]);
    mockCheckAccess.mockReturnValue(false);
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('returns 403 when non-admin tries to reopen', async () => {
    mockRequireAuth.mockResolvedValue([USER, null]);
    mockCheckAccess.mockReturnValue(false);
    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('returns 200 when admin approves', async () => {
    mockRequireAuth.mockResolvedValue([USER, null]);
    mockCheckAccess.mockReturnValue(true);
    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(200);
  });

  it('returns 200 when admin reopens', async () => {
    mockRequireAuth.mockResolvedValue([USER, null]);
    mockCheckAccess.mockReturnValue(true);
    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(200);
  });

  it('returns 200 when non-admin submits (no admin check needed)', async () => {
    mockRequireAuth.mockResolvedValue([USER, null]);
    const res = await POST(makeRequest({ op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockCheckAccess).not.toHaveBeenCalled();
  });
});
