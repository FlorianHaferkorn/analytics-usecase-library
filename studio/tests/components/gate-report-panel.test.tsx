import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { GateReportPanel } from '@/components/postcore/gate-report-panel';
import type { GenerateResult } from '@/lib/bridge/superversion-bridge';

const green: GenerateResult = {
  available: true,
  ok: true,
  bracket: 'COM-001_Sales_Performance',
  target: 'tmdl',
  targetLabel: 'TMDL semantic model',
  targetStatus: 'live',
  targetsAvailable: ['pbir', 'tmdl'],
  artifacts: [{ path: 'COM-001.SemanticModel/measures.tmdl', bytes: 512 }],
  gate: { ok: true, stages: [
    { name: 'source', status: 'PASS', detail: 'model built' },
    { name: 'pbir', status: 'SKIP', detail: 'CLI absent' },
  ] },
};

describe('GateReportPanel', () => {
  it('renders target picker, gate stages, artifacts, and offers handoff when green', () => {
    render(<GateReportPanel result={green} />);
    expect(screen.getByTestId('gate-report-panel')).toBeDefined();
    expect(screen.getByTestId('target-tmdl').getAttribute('aria-pressed')).toBe('true');
    expect(screen.getByTestId('target-pbir')).toBeDefined();
    expect(screen.getByTestId('stage-source').getAttribute('data-status')).toBe('PASS');
    expect(screen.getByTestId('stage-pbir').getAttribute('data-status')).toBe('SKIP');
    expect(screen.getByText(/measures\.tmdl/)).toBeDefined();
    expect(screen.getByTestId('deploy-handoff-ready')).toBeDefined();
    expect(screen.queryByTestId('deploy-handoff-blocked')).toBeNull();
  });

  it('blocks the handoff when the gate is red', () => {
    const red: GenerateResult = {
      ...green, ok: false,
      gate: { ok: false, stages: [{ name: 'pbir', status: 'FAIL', detail: '2 errors' }] },
    };
    render(<GateReportPanel result={red} />);
    expect(screen.getByTestId('gate-verdict').getAttribute('data-ok')).toBe('false');
    expect(screen.getByTestId('deploy-handoff-blocked')).toBeDefined();
    expect(screen.queryByTestId('deploy-handoff-ready')).toBeNull();
  });

  it('shows an honest unavailable banner when the bridge is down', () => {
    const down: GenerateResult = { available: false, ok: false, targetsAvailable: [], artifacts: [], error: 'Python bridge unavailable' };
    render(<GateReportPanel result={down} />);
    expect(screen.getByTestId('generate-unavailable')).toBeDefined();
    expect(screen.getByText(/nicht gate-validiert/)).toBeDefined();
    expect(screen.queryByTestId('gate-report-panel')).toBeNull();
  });
});
