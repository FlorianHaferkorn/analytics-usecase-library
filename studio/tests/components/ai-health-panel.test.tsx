import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AiHealthPanel } from '@/components/ai/ai-health-panel';
import type { AiHealth } from '@/lib/ai/health';

const base: AiHealth = {
  projectId: 'default',
  usage: { steps: 3, inputTokens: 1500, outputTokens: 400, costUsd: 0.012, uncomputedCostSteps: 0, unverifiedCostSteps: 0, errors: 0 },
  roi: { status: 'uncomputed', reason: 'no value proxies supplied (L2 data) — ROI not assumed', costUsd: 0.012, notes: [] },
  warnings: [],
};

describe('AiHealthPanel', () => {
  it('renders usage stats and cost', () => {
    render(<AiHealthPanel health={base} />);
    expect(screen.getByTestId('ai-health-panel')).toBeDefined();
    expect(screen.getByTestId('usage-stats').textContent).toContain('3');
    expect(screen.getByTestId('cost').textContent).toContain('$');
  });

  it('shows UNCOMPUTED ROI honestly when no value proxies', () => {
    render(<AiHealthPanel health={base} />);
    expect(screen.getByTestId('roi-verdict').getAttribute('data-status')).toBe('uncomputed');
    expect(screen.getByTestId('roi-uncomputed').textContent).toMatch(/UNCOMPUTED/);
  });

  it('renders a computed ROI as a percentage', () => {
    const h: AiHealth = {
      ...base,
      roi: { status: 'computed', roi: 2, netUsd: 0.024, costUsd: 0.012, valueUsd: 0.036, attribution: 1, includedProxies: ['timeUsd'], missingProxies: [], notes: [] },
    };
    render(<AiHealthPanel health={h} />);
    expect(screen.getByTestId('roi-verdict').getAttribute('data-status')).toBe('computed');
    expect(screen.getByText(/200%/)).toBeDefined();
  });

  it('surfaces honest warnings', () => {
    const h: AiHealth = { ...base, warnings: ['Kosten unvollständig: 2 Schritt(e) ohne Preis'] };
    render(<AiHealthPanel health={h} />);
    expect(screen.getByTestId('ai-health-warnings').textContent).toMatch(/unvollständig/);
  });
});
