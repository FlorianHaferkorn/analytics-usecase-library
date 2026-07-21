/**
 * Route-level auth guard tests for POST /api/ai-config
 * Verifies that `approve` AND `reopen` require admin RBAC, while `submit` does not.
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

beforeEach(() => {
  vi.clearAllMocks();
});

async function callPost(body: Record<string, unknown>) {
  const { POST } = await import('@/app/api/ai-config/route');
  const req = new Request('http://localhost/api/ai-config', {
    method: 'POST',
    body: JSON.stringify(body),
  });
  return POST(req);
}

describe('POST /api/ai-config — auth guards', () => {
  it('returns 401 when not authenticated', async () => {
    mockRequireAuth.mockResolvedValueOnce([null, new Response('Unauthorized', { status: 401 })]);
    const res = await callPost({ op: 'approve', layer: 'L1' });
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin attempts approve', async () => {
    mockRequireAuth.mockResolvedValueOnce([{ email: 'alice@example.com', name: 'Alice' }, null]);
    mockFindOrCreateUser.mockReturnValueOnce({ id: 'usr-alice' });
    mockCheckAccess.mockReturnValueOnce(false);
    const res = await callPost({ op: 'approve', layer: 'L1' });
    expect(res.status).toBe(403);
  });

  it('returns 403 when non-admin attempts reopen', async () => {
    mockRequireAuth.mockResolvedValueOnce([{ email: 'alice@example.com', name: 'Alice' }, null]);
    mockFindOrCreateUser.mockReturnValueOnce({ id: 'usr-alice' });
    mockCheckAccess.mockReturnValueOnce(false);
    const res = await callPost({ op: 'reopen', layer: 'L1' });
    expect(res.status).toBe(403);
  });

  it('returns 200 when admin approves', async () => {
    mockRequireAuth.mockResolvedValueOnce([{ email: 'admin@example.com', name: 'Admin' }, null]);
    mockFindOrCreateUser.mockReturnValueOnce({ id: 'usr-admin' });
    mockCheckAccess.mockReturnValueOnce(true);
    mockTransitionConfigLayer.mockReturnValueOnce({ status: 'approved' });
    const res = await callPost({ op: 'approve', layer: 'L1', justification: 'ok' });
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.layer.status).toBe('approved');
  });

  it('returns 200 when admin reopens', async () => {
    mockRequireAuth.mockResolvedValueOnce([{ email: 'admin@example.com', name: 'Admin' }, null]);
    mockFindOrCreateUser.mockReturnValueOnce({ id: 'usr-admin' });
    mockCheckAccess.mockReturnValueOnce(true);
    mockTransitionConfigLayer.mockReturnValueOnce({ status: 'draft' });
    const res = await callPost({ op: 'reopen', layer: 'L1', justification: 'needs work' });
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.layer.status).toBe('draft');
  });

  it('returns 200 when any authenticated user submits (no admin required)', async () => {
    mockRequireAuth.mockResolvedValueOnce([{ email: 'user@example.com', name: 'User' }, null]);
    mockTransitionConfigLayer.mockReturnValueOnce({ status: 'pending_review' });
    const res = await callPost({ op: 'submit', layer: 'L1', justification: 'please review' });
    expect(res.status).toBe(200);
    expect(mockCheckAccess).not.toHaveBeenCalled();
  });
});
