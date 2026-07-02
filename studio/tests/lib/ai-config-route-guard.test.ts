/**
 * Route-level RBAC guard tests for AI-Config governance (I-6.6).
 *
 * These tests verify that the POST /api/ai-config route enforces admin-only
 * access for operations that affect approved governance configs.  The
 * repository-layer invariants (two-person rule, schema validation, etc.) are
 * tested separately in ai-config-governance.test.ts.
 *
 * Critical bug (fixed): non-admin authenticated users could call `reopen` on
 * an approved config, moving it back to draft and silently disabling the
 * customer's governance policy.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { AiConfigLayer } from '@/lib/ai/config/resolve';

// ---- Mocks ----------------------------------------------------------------

vi.mock('@/lib/auth/session', () => ({
  requireAuth: vi.fn(),
}));
vi.mock('@/lib/db/rbac-repo', () => ({
  checkAccess: vi.fn(),
}));
vi.mock('@/lib/db/user-repo', () => ({
  findOrCreateUser: vi.fn(),
}));
vi.mock('@/lib/db/ai-config-repo', () => ({
  getConfigLayer: vi.fn(),
  upsertConfigLayer: vi.fn(),
  transitionConfigLayer: vi.fn(),
  AiConfigGovernanceError: class AiConfigGovernanceError extends Error {},
}));

// ---- Helpers ----------------------------------------------------------------

const APPROVED_ROW = {
  id: 'row-1', project_id: 'default', layer: 'L1', domain_id: '',
  config_json: '{}', schema_version: '1.0.0', status: 'approved',
  submitted_by: 'alice', approved_by: 'bob', justification: 'ok',
  effective_hash: 'abc123', created_at: '2026-01-01', updated_at: '2026-01-01',
};

const MOCK_USER = { email: 'carol@example.com', name: 'Carol' };
const MOCK_DB_USER = { id: 'usr-carol', email: 'carol@example.com', name: 'Carol' };

function makeRequest(body: Record<string, unknown>): Request {
  return new Request('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

async function getPostHandler() {
  // Fresh import per test to avoid module-cache cross-contamination.
  vi.resetModules();
  const { POST } = await import('@/app/api/ai-config/route');
  return POST;
}

// ---- Tests ---------------------------------------------------------------

describe('ai-config route RBAC guard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('non-admin user cannot reopen an approved config (governance bypass prevention)', async () => {
    const { requireAuth } = await import('@/lib/auth/session');
    const { checkAccess } = await import('@/lib/db/rbac-repo');
    const { findOrCreateUser } = await import('@/lib/db/user-repo');

    vi.mocked(requireAuth).mockResolvedValue([MOCK_USER as never, null]);
    vi.mocked(findOrCreateUser).mockReturnValue(MOCK_DB_USER as never);
    vi.mocked(checkAccess).mockReturnValue(undefined); // no admin access

    const POST = await getPostHandler();
    const req = makeRequest({ op: 'reopen', layer: 'L1' });
    const res = await POST(req);

    expect(res.status).toBe(403);
    const body = await res.json() as { error?: { message?: string } };
    expect(body.error?.message ?? '').toMatch(/admin/i);
  });

  it('admin user can reopen an approved config', async () => {
    const { requireAuth } = await import('@/lib/auth/session');
    const { checkAccess } = await import('@/lib/db/rbac-repo');
    const { findOrCreateUser } = await import('@/lib/db/user-repo');
    const { transitionConfigLayer } = await import('@/lib/db/ai-config-repo');

    vi.mocked(requireAuth).mockResolvedValue([MOCK_USER as never, null]);
    vi.mocked(findOrCreateUser).mockReturnValue(MOCK_DB_USER as never);
    vi.mocked(checkAccess).mockReturnValue({ user_id: 'usr-carol', project_id: 'default', role: 'admin' } as never);
    vi.mocked(transitionConfigLayer).mockReturnValue({ ...APPROVED_ROW, status: 'draft' } as never);

    const POST = await getPostHandler();
    const req = makeRequest({ op: 'reopen', layer: 'L1', justification: 'need change' });
    const res = await POST(req);

    expect(res.status).toBe(200);
    expect(transitionConfigLayer).toHaveBeenCalledWith('default', 'L1', '', 'reopen', MOCK_USER.email, 'need change');
  });

  it('non-admin user cannot approve (existing behavior, confirmed)', async () => {
    const { requireAuth } = await import('@/lib/auth/session');
    const { checkAccess } = await import('@/lib/db/rbac-repo');
    const { findOrCreateUser } = await import('@/lib/db/user-repo');

    vi.mocked(requireAuth).mockResolvedValue([MOCK_USER as never, null]);
    vi.mocked(findOrCreateUser).mockReturnValue(MOCK_DB_USER as never);
    vi.mocked(checkAccess).mockReturnValue(undefined);

    const POST = await getPostHandler();
    const req = makeRequest({ op: 'approve', layer: 'L1' });
    const res = await POST(req);

    expect(res.status).toBe(403);
    const body = await res.json() as { error?: { message?: string } };
    expect(body.error?.message ?? '').toMatch(/admin/i);
  });

  it('non-admin user can submit (no admin required)', async () => {
    const { requireAuth } = await import('@/lib/auth/session');
    const { transitionConfigLayer } = await import('@/lib/db/ai-config-repo');

    vi.mocked(requireAuth).mockResolvedValue([MOCK_USER as never, null]);
    vi.mocked(transitionConfigLayer).mockReturnValue({ ...APPROVED_ROW, status: 'review' } as never);

    const POST = await getPostHandler();
    const req = makeRequest({ op: 'submit', layer: 'L1' });
    const res = await POST(req);

    // submit is not admin-gated — should reach the repo (200 or governance error, not 403)
    expect(res.status).not.toBe(403);
  });
});
