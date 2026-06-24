import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DeliveryFlowPanel } from '@/components/postcore/delivery-flow-panel';
import type { DeliveryFlowState } from '@/lib/studio/delivery-flow';

const cleared: DeliveryFlowState = {
  bracketId: 'COM-001',
  canHandoff: true,
  blockedReason: null,
  steps: [
    { key: 'authoring', label: 'Authoring', status: 'done', detail: 'Bracket COM-001' },
    { key: 'approval', label: 'Freigabe-Schleuse', status: 'done', detail: 'freigegeben' },
    { key: 'generate', label: 'Generate', status: 'done', detail: '1 Artefakt · tmdl' },
    { key: 'validate', label: 'Validate (Gate)', status: 'done', detail: 'Gate grün' },
    { key: 'deliverable', label: 'Deliverable', status: 'done', detail: 'bereit' },
  ],
};

describe('DeliveryFlowPanel', () => {
  it('renders all five steps and enables handoff when cleared', () => {
    const onHandoff = vi.fn();
    render(<DeliveryFlowPanel flow={cleared} onHandoff={onHandoff} />);
    for (const key of ['authoring', 'approval', 'generate', 'validate', 'deliverable']) {
      expect(screen.getByTestId(`flow-step-${key}`).getAttribute('data-status')).toBe('done');
    }
    const btn = screen.getByTestId('flow-handoff');
    fireEvent.click(btn);
    expect(onHandoff).toHaveBeenCalledOnce();
    expect(screen.queryByTestId('flow-blocked')).toBeNull();
  });

  it('shows the blocking reason and no handoff button when blocked', () => {
    const blocked: DeliveryFlowState = {
      ...cleared,
      canHandoff: false,
      blockedReason: 'Nicht freigegeben (Freigabe-Schleuse offen)',
      steps: cleared.steps.map((s) => (s.key === 'approval' ? { ...s, status: 'pending', detail: 'Entwurf' } : s)),
    };
    render(<DeliveryFlowPanel flow={blocked} />);
    expect(screen.getByTestId('flow-blocked').textContent).toMatch(/Nicht freigegeben/);
    expect(screen.queryByTestId('flow-handoff')).toBeNull();
    expect(screen.getByTestId('flow-step-approval').getAttribute('data-status')).toBe('pending');
  });
});
