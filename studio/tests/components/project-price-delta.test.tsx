import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProjectPriceDelta } from '@/components/project/project-price-delta';
const hash = 'a'.repeat(64);
const totals = (cost: number) => ({ cost, price_calculated: cost * 1.5, price_rounded: cost * 1.5, list_price: cost * 1.6 });
const evaluated = (patch: Record<string, unknown> = {}) => ({ project_ref: 'alpha', baseline_revision_hash: hash, decision_ref: 'decision_environment_model', alternative_option_ref: 'dev_prod',
  status: 'evaluated', price_values_embedded: true, persist: false, currency: 'EUR', comparable: true,
  baseline: { packages: [], totals: totals(2000), priced_packages: 2, unpriced: [] },
  alternative: { packages: [], totals: totals(1500), priced_packages: 2, unpriced: [] },
  delta: { cost: -500, price_calculated: -750, price_rounded: -750, list_price: -800 }, ...patch });
const reply = (value: unknown, status = 200) => ({ ok: status < 400, status, json: async () => value }) as Response;
const props = { projectId: 'alpha', revisionHash: hash, decisionRef: 'decision_environment_model', optionRef: 'dev_prod' };
beforeEach(() => vi.stubGlobal('fetch', vi.fn(async () => reply(evaluated()))));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
describe('Price delta', () => {
  it('fetches only on explicit request', () => {
    render(<ProjectPriceDelta {...props} />);
    expect(fetch).not.toHaveBeenCalled();
    expect(screen.getByText(/never stored or exported/)).toBeTruthy();
  });
  it('shows baseline, alternative and signed delta', async () => {
    render(<ProjectPriceDelta {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show price delta' }));
    await screen.findByText(/Cost and price · accepted baseline → alternative/);
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toBe(`/api/projects/alpha/architecture/commercial/price?revision=${hash}&decision=decision_environment_model&option=dev_prod`);
    expect(screen.getByText('€2,000')).toBeTruthy();
    expect(screen.getByText('€1,500')).toBeTruthy();
    expect(screen.getByText('-€500')).toBeTruthy();
  });
  it('tells a non-admin why no price is shown', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ error: 'denied' }, 403));
    render(<ProjectPriceDelta {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show price delta' }));
    await screen.findByText('Only project admins can see prices.');
  });
  it('names unpriced packages instead of counting them as zero', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply(evaluated({ comparable: false,
      alternative: { packages: [], totals: totals(1500), priced_packages: 1, unpriced: [{ work_package_ref: 'wp_source_contracts', reason: 'Time-and-material packages are not priced.' }] } })));
    render(<ProjectPriceDelta {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show price delta' }));
    await screen.findByText('Time-and-material packages are not priced.');
    expect(screen.getByText(/Not fully comparable/)).toBeTruthy();
  });
  it('rejects a result that could be persisted', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply(evaluated({ persist: true })));
    render(<ProjectPriceDelta {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show price delta' }));
    await screen.findByText('Price delta project, revision or option mismatch');
  });
});
