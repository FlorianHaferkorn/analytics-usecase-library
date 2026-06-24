import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PreCorePanel } from '@/components/precore/precore-panel';
import type { PreCoreResult } from '@/lib/bridge/superversion-bridge';

const available: PreCoreResult = {
  available: true,
  ok: true,
  bracket: 'COM-001_Sales_Performance',
  engines: [
    {
      id: 'dataarch', label: 'Data-architecture audit (Beta)', status: 'beta', ok: true,
      counts: { info: 1, warn: 0, error: 0 },
      findings: [{ severity: 'info', code: 'ARCH_NO_DATE_TABLE', detail: 'no date table marked' }],
    },
    {
      id: 'gov', label: 'Governance audit (Beta)', status: 'beta', ok: true,
      counts: { info: 0, warn: 0, error: 0 }, findings: [],
    },
  ],
};

describe('PreCorePanel', () => {
  it('renders engine findings from the core verdict', () => {
    render(<PreCorePanel result={available} />);
    expect(screen.getByTestId('precore-panel')).toBeDefined();
    expect(screen.getByTestId('engine-dataarch')).toBeDefined();
    expect(screen.getByText(/ARCH_NO_DATE_TABLE/)).toBeDefined();
    // engine with no findings shows the clean marker, not a fabricated issue
    expect(screen.getByTestId('engine-gov-clean')).toBeDefined();
  });

  it('shows an honest unavailable banner when the bridge is down', () => {
    const down: PreCoreResult = { available: false, ok: false, engines: [], error: 'Python bridge unavailable (python3 not found)' };
    render(<PreCorePanel result={down} />);
    expect(screen.getByTestId('precore-unavailable')).toBeDefined();
    expect(screen.getByText(/nicht gate-validiert/)).toBeDefined();
    expect(screen.queryByTestId('precore-panel')).toBeNull();
  });
});
