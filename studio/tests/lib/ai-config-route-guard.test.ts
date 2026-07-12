/**
 * Route-level guard tests for POST /api/ai-config.
 *
 * Verifies that approve AND reopen both require admin (the reopen bypass was a
 * recurring governance vulnerability: only approve was guarded, leaving reopen
 * reachable by any authenticated user).
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

const { mockRequireAuth, mockCheckAccess, mockFindOrCreateUser, mockTransition, mockGetConfigLayer } =
  vi.hoisted(() => ({
    mockRequireAuth: vi.fn(),
    mockCheckAccess: vi.fn(),
    mockFindOrCreateUser: vi.fn(),
    mockTransition: vi.fn(),
    mockGetConfigLayer: vi.fn(),
  }));

vi.mock('@/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));
vi.mock('@/lib/db/rbac-repo', () => ({ checkAccess: mockCheckAccess }));
vi.mock('@/lib/db/user-repo', () => ({ findOrCreateUser: mockFindOrCreateUser }));
vi.mock('@/lib/db/ai-config-repo', () => ({
  getConfigLayer: mockGetConfigLayer,
  upsertConfigLayer: vi.fn(() => ({ status: 'draft' })),
  transitionConfigLayer: mockTransition,
  AiConfigGovernanceError: class AiConfigGovernanceError extends Error {},
}));

import { POST } from '@/app/api/ai-config/route';

const AUTHED_USER = { email: 'user@test.com', name: 'Test User' };
const DB_USER = { id: 'usr-1', email: 'user@test.com', name: 'Test User' };
const LAYER_ROW = { id: 'cfg-1', status: 'draft' };

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
  mockTransition.mockReturnValue(LAYER_ROW);
  mockGetConfigLayer.mockReturnValue(LAYER_ROW);
});

describe('POST /api/ai-config — admin guard', () => {
  it('returns 401 when unauthenticated', async () => {
    const authErr = new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
    mockRequireAuth.mockResolvedValue([null, authErr]);

    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(401);
  });

  it('returns 403 when non-admin attempts approve', async () => {
    mockRequireAuth.mockResolvedValue([AUTHED_USER, null]);
    mockCheckAccess.mockReturnValue(undefined); // not admin

    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(403);
    expect(mockTransition).not.toHaveBeenCalled();
  });

  it('returns 403 when non-admin attempts reopen (governance bypass fix)', async () => {
    mockRequireAuth.mockResolvedValue([AUTHED_USER, null]);
    mockCheckAccess.mockReturnValue(undefined); // not admin

    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(403);
    expect(mockTransition).not.toHaveBeenCalled();
  });

  it('returns 200 when admin approves', async () => {
    mockRequireAuth.mockResolvedValue([AUTHED_USER, null]);
    mockCheckAccess.mockReturnValue({ id: 'usr-1', role: 'admin' }); // is admin

    const res = await POST(makeRequest({ op: 'approve', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockTransition).toHaveBeenCalledWith('default', 'L1', '', 'approve', AUTHED_USER.email, '');
  });

  it('returns 200 when admin reopens', async () => {
    mockRequireAuth.mockResolvedValue([AUTHED_USER, null]);
    mockCheckAccess.mockReturnValue({ id: 'usr-1', role: 'admin' }); // is admin

    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockTransition).toHaveBeenCalledWith('default', 'L1', '', 'reopen', AUTHED_USER.email, '');
  });

  it('returns 200 when any authenticated user submits (submit is not admin-gated)', async () => {
    mockRequireAuth.mockResolvedValue([AUTHED_USER, null]);

    const res = await POST(makeRequest({ op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(mockCheckAccess).not.toHaveBeenCalled();
  });
});
