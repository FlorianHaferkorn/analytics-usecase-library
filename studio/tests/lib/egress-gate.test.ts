/**
 * The AI egress gate answers in the standard error shape { error: { code, message } },
 * with the audit evidence id inside `error`.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';

const h = vi.hoisted(() => ({ persist: vi.fn(), failPersist: false }));
vi.mock('@/lib/ai/egress-preflight', () => ({
  buildAiEgressEvidence: () => ({ event_id: 'evt-1' }),
  persistAiEgressEvidence: (...args: unknown[]) => {
    h.persist(...args);
    if (h.failPersist) throw new Error('disk full');
  },
}));

import { requireApprovedAiEgress } from '@/lib/ai/egress-gate';

describe('requireApprovedAiEgress', () => {
  beforeEach(() => { h.persist.mockReset(); h.failPersist = false; });

  it('denies with 403 AI_EGRESS_NOT_APPROVED and the evidence id', async () => {
    const res = requireApprovedAiEgress({ projectId: 'p-1' });
    expect(res?.status).toBe(403);
    const body = await res!.json();
    expect(body.error).toMatchObject({ code: 'AI_EGRESS_NOT_APPROVED', evidenceId: 'evt-1' });
    expect(body.error.message).toMatch(/paused for this project/);
    expect(h.persist).toHaveBeenCalledWith({ event_id: 'evt-1' }, 'p-1', 'system');
  });

  it('refuses with 503 AI_EGRESS_AUDIT_FAILED when the evidence cannot be persisted', async () => {
    h.failPersist = true;
    const res = requireApprovedAiEgress();
    expect(res?.status).toBe(503);
    expect(await res!.json()).toEqual({
      error: { code: 'AI_EGRESS_AUDIT_FAILED', message: 'AI processing is paused because the security evidence could not be persisted.' },
    });
  });
});
