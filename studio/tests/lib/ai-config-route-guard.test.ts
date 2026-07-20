/**
 * Route-level guard tests for POST /api/ai-config.
 * Verifies that `approve` and `reopen` require admin RBAC, while `submit` does not.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

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

const ADMIN_USER = { id: 'usr-admin', email: 'admin@co.com', name: 'Admin' };
const NON_ADMIN_USER = { id: 'usr-editor', email: 'editor@co.com', name: 'Editor' };
const DB_USER = { id: 'usr-001', email: 'admin@co.com', name: 'Admin' };

async function callPost(body: Record<string, unknown>) {
  const { POST } = await import('@/app/api/ai-config/route');
  return POST(new Request('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }));
}

describe('POST /api/ai-config — route guard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
    mockFindOrCreateUser.mockReturnValue(DB_USER);
    mockTransitionConfigLayer.mockReturnValue({ id: 'layer-1', status: 'approved' });
  });

  it('returns 401 when not authenticated', async () => {
    mockRequireAuth.mockResolvedValue([null, new Response('Unauthorized', { status: 401 })]);
    const res = await callPost({ op: 'approve', layer: 'L1' });
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin attempts approve', async () => {
    mockRequireAuth.mockResolvedValue([NON_ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(null);
    const res = await callPost({ op: 'approve', layer: 'L1', justification: 'ok' });
    expect(res.status).toBe(403);
  });

  it('returns 403 when non-admin attempts reopen', async () => {
    mockRequireAuth.mockResolvedValue([NON_ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue(null);
    const res = await callPost({ op: 'reopen', layer: 'L1', justification: 'needs rework' });
    expect(res.status).toBe(403);
  });

  it('returns 200 when admin approves', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue({ role: 'admin' });
    const res = await callPost({ op: 'approve', layer: 'L1', justification: 'lgtm' });
    expect(res.status).toBe(200);
    expect(mockTransitionConfigLayer).toHaveBeenCalledWith('default', 'L1', '', 'approve', ADMIN_USER.email, 'lgtm');
  });

  it('returns 200 when admin reopens', async () => {
    mockRequireAuth.mockResolvedValue([ADMIN_USER, null]);
    mockCheckAccess.mockReturnValue({ role: 'admin' });
    const res = await callPost({ op: 'reopen', layer: 'L1', justification: 'needs update' });
    expect(res.status).toBe(200);
    expect(mockTransitionConfigLayer).toHaveBeenCalledWith('default', 'L1', '', 'reopen', ADMIN_USER.email, 'needs update');
  });

  it('returns 200 when any authenticated user submits (no admin required)', async () => {
    mockRequireAuth.mockResolvedValue([NON_ADMIN_USER, null]);
    const res = await callPost({ op: 'submit', layer: 'L1', justification: 'please review' });
    expect(res.status).toBe(200);
    expect(mockCheckAccess).not.toHaveBeenCalled();
  });
});
