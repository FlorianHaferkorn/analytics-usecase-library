/**
 * Route-level RBAC guard tests for /api/ai-config.
 *
 * These tests verify that `approve` and `reopen` require admin role,
 * while `submit`, `reject`, and `save` do not.
 *
 * Critical invariant: `reopen` moves an approved layer back to draft,
 * bypassing customer AI policy — it MUST be admin-gated.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { NextRequest } from 'next/server';

/* ------------------------------------------------------------------ */
/* hoisted mocks (must be before vi.mock factories)                    */
/* ------------------------------------------------------------------ */

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

const ALICE: import('@/lib/auth/session').SessionUser = { id: 'u1', email: 'alice@co', name: 'Alice' };
const ALICE_DB = { id: 'u1', email: 'alice@co', name: 'Alice' };
const STUB_LAYER = { id: 'l1', status: 'draft' };

function req(body: Record<string, unknown>) {
  return new NextRequest('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  mockRequireAuth.mockResolvedValue([ALICE, null]);
  mockFindOrCreateUser.mockReturnValue(ALICE_DB);
  mockTransitionConfigLayer.mockReturnValue(STUB_LAYER);
  mockUpsertConfigLayer.mockReturnValue(STUB_LAYER);
  mockGetConfigLayer.mockReturnValue(STUB_LAYER);
});

describe('POST /api/ai-config — admin guard', () => {
  it('blocks non-admin from approve', async () => {
    mockCheckAccess.mockReturnValue(false); // non-admin
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(req({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
    const body = await res.json();
    expect(body.error).toBeDefined();
  });

  it('blocks non-admin from reopen', async () => {
    mockCheckAccess.mockReturnValue(false); // non-admin
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(req({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
    const body = await res.json();
    expect(body.error).toBeDefined();
  });

  it('allows admin to approve', async () => {
    mockCheckAccess.mockReturnValue(true); // admin
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(req({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockTransitionConfigLayer).toHaveBeenCalledWith('default', 'L1', '', 'approve', ALICE.email, '');
  });

  it('allows admin to reopen', async () => {
    mockCheckAccess.mockReturnValue(true); // admin
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(req({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockTransitionConfigLayer).toHaveBeenCalledWith('default', 'L1', '', 'reopen', ALICE.email, '');
  });

  it('allows any authenticated user to submit (no admin check)', async () => {
    // checkAccess should NOT be called for submit
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(req({ op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockCheckAccess).not.toHaveBeenCalled();
  });

  it('rejects unauthenticated requests immediately', async () => {
    mockRequireAuth.mockResolvedValue([null, new Response('{}', { status: 401 })]);
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(req({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(401);
    expect(mockCheckAccess).not.toHaveBeenCalled();
  });
});
