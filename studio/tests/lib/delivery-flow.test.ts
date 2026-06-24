import { describe, it, expect } from 'vitest';
import { computeDeliveryFlow, type DeliveryFlowInputs } from '@/lib/studio/delivery-flow';
import type { GenerateResult } from '@/lib/bridge/superversion-bridge';

const greenGen: GenerateResult = {
  available: true,
  ok: true,
  bracket: 'COM-001',
  target: 'tmdl',
  targetsAvailable: ['pbir', 'tmdl'],
  artifacts: [{ path: 'm.tmdl', bytes: 100 }],
  gate: { ok: true, stages: [{ name: 'source', status: 'PASS', detail: '' }] },
};

function flow(p: Partial<DeliveryFlowInputs>) {
  return computeDeliveryFlow({ bracketId: 'COM-001', bracketExists: true, approval: 'draft', generate: null, ...p });
}

const step = (f: ReturnType<typeof flow>, key: string) => f.steps.find((s) => s.key === key)!;

describe('computeDeliveryFlow — customer-without-builder journey', () => {
  it('blocks at authoring when the bracket does not exist', () => {
    const f = flow({ bracketExists: false, approval: null });
    expect(step(f, 'authoring').status).toBe('blocked');
    expect(f.canHandoff).toBe(false);
    expect(f.blockedReason).toMatch(/Kein Bracket/);
  });

  it('draft bracket: authoring done, deliverable blocked on Freigabe', () => {
    const f = flow({ approval: 'draft' });
    expect(step(f, 'authoring').status).toBe('done');
    expect(step(f, 'approval').status).toBe('pending');
    expect(f.blockedReason).toMatch(/Nicht freigegeben/);
  });

  it('in review: approval current, still blocked', () => {
    const f = flow({ approval: 'review' });
    expect(step(f, 'approval').status).toBe('current');
    expect(f.canHandoff).toBe(false);
  });

  it('approved but not yet generated: blocked on generation', () => {
    const f = flow({ approval: 'approved', generate: null });
    expect(step(f, 'approval').status).toBe('done');
    expect(step(f, 'generate').status).toBe('pending');
    expect(f.blockedReason).toMatch(/nicht gelaufen/);
  });

  it('approved + green gate: the full journey clears, handoff allowed', () => {
    const f = flow({ approval: 'approved', generate: greenGen });
    expect(f.steps.map((s) => s.status)).toEqual(['done', 'done', 'done', 'done', 'done']);
    expect(f.canHandoff).toBe(true);
    expect(f.blockedReason).toBeNull();
  });

  it('approved but red gate: validate blocked, deliverable blocked', () => {
    const redGen: GenerateResult = {
      ...greenGen, ok: false,
      gate: { ok: false, stages: [{ name: 'pbir', status: 'FAIL', detail: '2 errors' }] },
    };
    const f = flow({ approval: 'approved', generate: redGen });
    expect(step(f, 'validate').status).toBe('blocked');
    expect(step(f, 'validate').detail).toMatch(/pbir/);
    expect(f.canHandoff).toBe(false);
    expect(f.blockedReason).toMatch(/Gate rot/);
  });

  it('approved but bridge offline: generate blocked honestly', () => {
    const offline: GenerateResult = { available: false, ok: false, targetsAvailable: [], artifacts: [], error: 'bridge offline' };
    const f = flow({ approval: 'approved', generate: offline });
    expect(step(f, 'generate').status).toBe('blocked');
    expect(step(f, 'validate').status).toBe('pending');
    expect(f.canHandoff).toBe(false);
  });

  it('rejected bracket: approval blocked with rework hint', () => {
    const f = flow({ approval: 'rejected' });
    expect(step(f, 'approval').status).toBe('blocked');
    expect(step(f, 'approval').detail).toMatch(/abgelehnt/);
  });
});
