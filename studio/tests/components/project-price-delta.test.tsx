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
      alternative: { packages: [], totals: totals(1500), priced_packages: 1, unpriced: [{ work_package_ref: 'wp_source_contracts', reason: 'Time-and-material package cannot be banded: no rate mix.' }] } })));
    render(<ProjectPriceDelta {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show price delta' }));
    await screen.findByText('Time-and-material package cannot be banded: no rate mix.');
    expect(screen.getByText(/Not fully comparable/)).toBeTruthy();
  });
  it('shows time and material as a band outside the totals', async () => {
    const row = { work_package_ref: 'wp_source_contracts', package_ref: 'REF_SOURCES', hours_band: [40, 60], blended_rate: 100,
      rate_mix: { engineer_nearshore: 1 }, rate_mix_source: 'Paket: satzklassen_anteil', price_band: [4000, 6000], status: 'Annahme' };
    vi.mocked(fetch).mockResolvedValueOnce(reply(evaluated({
      baseline: { packages: [], totals: totals(2000), priced_packages: 1, unpriced: [], time_and_material: [row], time_and_material_price_band: [4000, 6000] },
      alternative: { packages: [], totals: totals(1500), priced_packages: 1, unpriced: [], time_and_material: [row], time_and_material_price_band: [4000, 6000] },
    })));
    render(<ProjectPriceDelta {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show price delta' }));
    await screen.findByText('Time and material (band, not in the totals above)');
    expect(screen.getAllByText('\u20ac4,000 \u2013 \u20ac6,000 (40\u201360 h at \u20ac100/h)')).toHaveLength(2);
    expect(screen.getAllByText('\u20ac4,000 \u2013 \u20ac6,000')).toHaveLength(2);
    expect(screen.getByText('\u20ac2,000')).toBeTruthy();
  });
  it('rejects a result that could be persisted', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply(evaluated({ persist: true })));
    render(<ProjectPriceDelta {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show price delta' }));
    await screen.findByText('Price delta project, revision or option mismatch');
  });
});
