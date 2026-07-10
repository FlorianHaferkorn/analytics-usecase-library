/**
 * Route-level RBAC guard tests for POST /api/ai-config.
 *
 * Verifies that:
 *   - Unauthenticated requests → 401
 *   - Non-admin `approve` → 403
 *   - Non-admin `reopen`  → 403  (regression: was missing before fix)
 *   - Admin `approve`     → 200
 *   - Admin `reopen`      → 200
 *   - Non-admin `submit`  → 200  (submit is not admin-gated)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

// vi.hoisted() ensures these refs are available inside vi.mock() factories,
// which are hoisted above all imports by Vitest.
const { mockRequireAuth, mockCheckAccess, mockFindOrCreateUser, mockTransition } = vi.hoisted(() => ({
  mockRequireAuth: vi.fn(),
  mockCheckAccess: vi.fn(),
  mockFindOrCreateUser: vi.fn(),
  mockTransition: vi.fn(),
}));

vi.mock('@/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));
vi.mock('@/lib/db/rbac-repo', () => ({ checkAccess: mockCheckAccess }));
vi.mock('@/lib/db/user-repo', () => ({ findOrCreateUser: mockFindOrCreateUser }));
vi.mock('@/lib/db/ai-config-repo', () => ({
  getConfigLayer: vi.fn(() => ({ status: 'draft' })),
  upsertConfigLayer: vi.fn(() => ({ status: 'draft' })),
  transitionConfigLayer: mockTransition,
  AiConfigGovernanceError: class AiConfigGovernanceError extends Error {},
}));

import { POST } from '@/app/api/ai-config/route';

const ADMIN = { id: 'u1', email: 'admin@co.com', name: 'Admin' };
const EDITOR = { id: 'u2', email: 'editor@co.com', name: 'Editor' };

function makeReq(body: Record<string, unknown>): Request {
  return new Request('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  mockTransition.mockReturnValue({ status: 'pending' });
  mockFindOrCreateUser.mockReturnValue({ id: 'u1' });
});

describe('POST /api/ai-config — auth guard', () => {
  it('returns 401 when request is unauthenticated', async () => {
    mockRequireAuth.mockResolvedValueOnce([null, new Response(null, { status: 401 })]);
    const res = await POST(makeReq({ op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(401);
  });
});

describe('POST /api/ai-config — admin RBAC guard', () => {
  it('returns 403 when non-admin tries to approve', async () => {
    mockRequireAuth.mockResolvedValueOnce([EDITOR, null]);
    mockCheckAccess.mockReturnValueOnce(false);
    const res = await POST(makeReq({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('returns 403 when non-admin tries to reopen', async () => {
    mockRequireAuth.mockResolvedValueOnce([EDITOR, null]);
    mockCheckAccess.mockReturnValueOnce(false);
    const res = await POST(makeReq({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
  });

  it('returns 200 when admin approves', async () => {
    mockRequireAuth.mockResolvedValueOnce([ADMIN, null]);
    mockCheckAccess.mockReturnValueOnce(true);
    const res = await POST(makeReq({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(200);
  });

  it('returns 200 when admin reopens', async () => {
    mockRequireAuth.mockResolvedValueOnce([ADMIN, null]);
    mockCheckAccess.mockReturnValueOnce(true);
    const res = await POST(makeReq({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(200);
  });

  it('returns 200 when non-admin submits (submit is not admin-gated)', async () => {
    mockRequireAuth.mockResolvedValueOnce([EDITOR, null]);
    const res = await POST(makeReq({ op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(200);
  });
});
