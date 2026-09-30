import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SimulatorClient } from '@/app/(studio)/simulator/simulator-client';

vi.mock('@/lib/hooks/use-domain-filter', () => ({ useDomainFilter: () => ({ domainFilter: null }) }));
vi.mock('@/components/ai/ai-field', () => ({ AiField: () => <textarea aria-label="Impact logic draft" /> }));
vi.mock('@/components/compose/spine-context-card', () => ({ SpineContextCard: () => <div>Decision context</div> }));

const bracket = { id: 'EXAMPLE', title: 'Working capital example', domain: 'finance', formula: 'KPI-FIN-006 = KPI-FIN-001 + KPI-FIN-004 - KPI-FIN-005', impactDirection: 'minimize' as const, strategicKpiId: 'KPI-FIN-006', influencingKpiIds: ['KPI-FIN-001', 'KPI-FIN-004', 'KPI-FIN-005'], impactLogic: 'Example logic' };

describe('Simulator workbench hierarchy', () => {
  it('keeps data limitations visible while putting controls and results before context', () => {
    render(<SimulatorClient brackets={[bracket]} spines={[]} />);
    const warning = screen.getByText(/Baseline values are synthetic/);
    expect(warning.closest('details')).toBeNull();
    const selector = screen.getByRole('combobox');
    const result = screen.getByRole('heading', { name: 'Simulation Result' });
    const adjustments = screen.getByRole('heading', { name: 'Driver Adjustments' });
    const details = screen.getByText('Assumptions, decision context and impact logic').closest('details');
    expect(details?.open).toBe(false);
    expect(selector.compareDocumentPosition(result) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(adjustments.compareDocumentPosition(details!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getByLabelText('Impact logic draft').closest('details')).toBe(details);
  });

  it('does not imply every showcase baseline is observed data', () => {
    render(<SimulatorClient brackets={[bracket]} spines={[]} auroraLinked />);
    expect(screen.getByText(/remaining values are synthetic/)).toBeTruthy();
  });

  it('presents unchanged results neutrally with consistent target and baseline units', () => {
    render(<SimulatorClient brackets={[{ ...bracket, formula: 'KPI-COM-013 = f(KPI-COM-005)', strategicKpiId: 'KPI-COM-013' }]} spines={[]} auroraLinked auroraKpis={{
      'KPI-COM-013': { value: 37.5, previousValue: 36, target: 40, unit: '%', trend: [] },
      'KPI-COM-005': { value: 901742929.3, previousValue: 800000000, target: 950000000, unit: 'EUR', trend: [] },
    }} />);
    expect(screen.getAllByText('37,5%')).toHaveLength(2);
    const result = screen.getByRole('heading', { name: 'Simulation Result' }).closest('section');
    expect(result?.getAttribute('data-tone')).toBe('default');
    expect(result?.textContent).toContain('No change');
    expect(screen.getByText('901.742.929 € (no change)')).toBeTruthy();
  });
});
