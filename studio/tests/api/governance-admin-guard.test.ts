/**
 * The admin gate on the governance route handlers — tested at the route, on purpose.
 *
 * A test on the ADMIN_ACTIONS map alone would stay green while the route ignored it;
 * that is the "gate that measures nothing" failure. So these cases call the exported
 * POST handlers and assert on two things at once: the 403, and that the workflow
 * function underneath was never reached.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

const h = vi.hoisted(() => ({
  istAdmin: true,
  transitionConfigLayer: vi.fn(() => ({ status: 'draft' })),
  decideRefinement: vi.fn(() => ({ status: 'rejected' })),
}));

vi.mock('@/lib/auth/session', () => ({
  requireAuth: async () => [{ email: 'mallory@example.com', name: 'Mallory' }, null],
}));
vi.mock('@/lib/auth/require-role', () => ({
  requireRole: async () => [{ email: 'mallory@example.com', name: 'Mallory' }, null],
}));
vi.mock('@/lib/db/user-repo', () => ({
  findOrCreateUser: () => ({ id: 'u-mallory', email: 'mallory@example.com' }),
}));
vi.mock('@/lib/db/rbac-repo', () => ({
  checkAccess: (_p: string, _u: string, rolle: string) => (rolle === 'admin' ? h.istAdmin : true),
}));
vi.mock('@/lib/db/ai-config-repo', () => ({
  getConfigLayer: () => null,
  upsertConfigLayer: vi.fn(),
  transitionConfigLayer: h.transitionConfigLayer,
  AiConfigGovernanceError: class extends Error {},
}));
vi.mock('@/lib/governance/refinement-workflow', () => ({
  decideRefinement: h.decideRefinement,
  listRefinements: () => [],
}));

function post(url: string, body: unknown): Request {
  return new Request(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });
}

beforeEach(() => {
  h.istAdmin = true;
  h.transitionConfigLayer.mockClear();
  h.decideRefinement.mockClear();
});

describe('ai-config governance route', () => {
  // reopen is the one the guard used to miss: it takes an approved layer back to
  // draft, and getApprovedLayers() stops serving it from that moment on.
  for (const op of ['approve', 'reject', 'reopen'] as const) {
    it(`refuses '${op}' for a non-admin and does not touch the layer`, async () => {
      h.istAdmin = false;
      const { POST } = await import('@/app/api/ai-config/route');
      const res = await POST(post('http://x/api/ai-config', { op, layer: 'L1' }));
      expect(res.status).toBe(403);
      expect(h.transitionConfigLayer).not.toHaveBeenCalled();
    });

    it(`lets an admin '${op}'`, async () => {
      const { POST } = await import('@/app/api/ai-config/route');
      const res = await POST(post('http://x/api/ai-config', { op, layer: 'L1' }));
      expect(res.status).toBe(200);
      expect(h.transitionConfigLayer).toHaveBeenCalledOnce();
    });
  }

  it("leaves 'submit' open to a non-admin — proposing is not deciding", async () => {
    h.istAdmin = false;
    const { POST } = await import('@/app/api/ai-config/route');
    const res = await POST(post('http://x/api/ai-config', { op: 'submit', layer: 'L1' }));
    expect(res.status).toBe(200);
    expect(h.transitionConfigLayer).toHaveBeenCalledOnce();
  });
});

describe('wirkung refinements route', () => {
  for (const action of ['approve', 'reject'] as const) {
    it(`refuses '${action}' for a non-admin and does not decide the proposal`, async () => {
      h.istAdmin = false;
      const { POST } = await import('@/app/api/wirkung/refinements/route');
      const res = await POST(post('http://x/api/wirkung/refinements', {
        proposalKey: 'AC-1::KPI-1', action,
      }));
      expect(res.status).toBe(403);
      expect(h.decideRefinement).not.toHaveBeenCalled();
    });

    it(`lets an admin '${action}'`, async () => {
      const { POST } = await import('@/app/api/wirkung/refinements/route');
      const res = await POST(post('http://x/api/wirkung/refinements', {
        proposalKey: 'AC-1::KPI-1', action,
      }));
      expect(res.status).toBe(200);
      expect(h.decideRefinement).toHaveBeenCalledOnce();
    });
  }
});
