/**
 * Route-level RBAC guard tests for /api/ai-config (POST).
 *
 * Invariant: `approve` and `reopen` require admin role; all other ops
 * (save, submit, reject) are open to any authenticated user.
 * An unauthenticated request must receive 401 before any op is dispatched.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

// ── hoisted mock state (must be initialised before vi.mock factories run) ─────
const { mockRequireAuth, mockCheckAccess, mockFindOrCreateUser, mockTransition } = vi.hoisted(() => ({
  mockRequireAuth: vi.fn(),
  mockCheckAccess: vi.fn(),
  mockFindOrCreateUser: vi.fn(),
  mockTransition: vi.fn(),
}));

vi.mock('../../src/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));
vi.mock('../../src/lib/db/rbac-repo', () => ({ checkAccess: mockCheckAccess }));
vi.mock('../../src/lib/db/user-repo', () => ({ findOrCreateUser: mockFindOrCreateUser }));
vi.mock('../../src/lib/db/ai-config-repo', () => ({
  getConfigLayer: vi.fn().mockReturnValue(null),
  upsertConfigLayer: vi.fn().mockReturnValue({ status: 'draft' }),
  transitionConfigLayer: mockTransition,
  AiConfigGovernanceError: class AiConfigGovernanceError extends Error {},
}));

import { POST } from '../../src/app/api/ai-config/route';

// ── helpers ───────────────────────────────────────────────────────────────────

const ALICE = { id: 'u-alice', email: 'alice@example.com', name: 'Alice' };
const BOB   = { id: 'u-bob',   email: 'bob@example.com',   name: 'Bob'   };

function asRequest(body: object): Request {
  return new Request('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

function asUnauth(): Response {
  return new Response(JSON.stringify({ error: 'Authentication required' }), { status: 401 });
}

beforeEach(() => {
  vi.clearAllMocks();
  mockFindOrCreateUser.mockReturnValue({ id: 'u-alice' });
  mockTransition.mockReturnValue({ status: 'submitted' });
});

// ── tests ─────────────────────────────────────────────────────────────────────

describe('ai-config route — auth guard', () => {
  it('returns 401 when the request is unauthenticated', async () => {
    mockRequireAuth.mockResolvedValue([null, asUnauth()]);

    const res = await POST(asRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when a non-admin tries to approve', async () => {
    mockRequireAuth.mockResolvedValue([ALICE, null]);
    mockCheckAccess.mockReturnValue(undefined); // no admin membership

    const res = await POST(asRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
    expect(mockTransition).not.toHaveBeenCalled();
  });

  it('returns 403 when a non-admin tries to reopen (governance bypass bug)', async () => {
    mockRequireAuth.mockResolvedValue([ALICE, null]);
    mockCheckAccess.mockReturnValue(undefined); // no admin membership

    const res = await POST(asRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
    expect(mockTransition).not.toHaveBeenCalled();
  });

  it('allows an admin to approve', async () => {
    mockRequireAuth.mockResolvedValue([BOB, null]);
    mockCheckAccess.mockReturnValue({ role: 'admin' }); // admin

    const res = await POST(asRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockTransition).toHaveBeenCalledWith('default', 'L1', '', 'approve', BOB.email, '');
  });

  it('allows an admin to reopen', async () => {
    mockRequireAuth.mockResolvedValue([BOB, null]);
    mockCheckAccess.mockReturnValue({ role: 'admin' }); // admin

    const res = await POST(asRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockTransition).toHaveBeenCalledWith('default', 'L1', '', 'reopen', BOB.email, '');
  });

  it('allows a non-admin to submit (submit is not admin-gated)', async () => {
    mockRequireAuth.mockResolvedValue([ALICE, null]);
    // checkAccess is NOT called for submit — verifying no admin guard is applied
    mockTransition.mockReturnValue({ status: 'submitted' });

    const res = await POST(asRequest({ op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockCheckAccess).not.toHaveBeenCalled();
    expect(mockTransition).toHaveBeenCalledWith('default', 'L1', '', 'submit', ALICE.email, '');
  });
});
