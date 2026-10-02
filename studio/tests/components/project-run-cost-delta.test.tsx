import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProjectRunCostDelta } from '@/components/project/project-run-cost-delta';
const hash = 'a'.repeat(64);
const cap = (id: string, sku: string, perMonth: number, environments: string[]) => ({ capacity_id: id, sku, billing: 'payg', price_basis: 'region:westeurope',
  environments, per_month: perMonth, overage: { enabled: false, threshold_source: 'customer', max_per_month: 0 } });
const licences = { authors: 5, viewers: 200, production_sku: 'F64', viewers_need_pro: false, pro_users: 5, pro_per_user_month: 14,
  per_month: 70, basis: 'production SKU F64 or larger: viewers without licence' };
const storage = { retained_gb: 40, per_gb_month: 0.024, per_month: 1 };
const side = (caps: ReturnType<typeof cap>[], patch: Record<string, unknown> = {}) => {
  const capacity = caps.reduce((sum, row) => sum + row.per_month, 0);
  return { currency: 'USD', capacities: caps, capacity_per_month: capacity, licences, monitoring_storage: storage, per_month: capacity + 71,
    overage_ceiling_per_month: 0, priced_capacities: caps.length, unpriced: [] as Array<{ item: string; reason: string }>, ...patch };
};
const evaluated = (patch: Record<string, unknown> = {}) => ({ project_ref: 'alpha', baseline_revision_hash: hash, decision_ref: 'decision_environment_model',
  alternative_option_ref: 'dev_prod', status: 'evaluated', persist: false, currency: 'USD', region: 'West Europe',
  price_basis: 'Microsoft list price, regional rate (Azure Retail Prices API)', price_valid_from: '2026-10-01', comparable: true,
  baseline: side([cap('p', 'F64', 8000, ['prod']), cap('t', 'F16', 2000, ['test'])]),
  alternative: side([cap('p', 'F64', 8000, ['prod'])]),
  delta: { per_month: -2000, per_year: -24000, capacity_per_month: -2000, licence_per_month: 0, monitoring_storage_per_month: 0,
    overage_ceiling_per_month: 0, capacities_removed: ['t'], capacities_added: [] }, ...patch });
const reply = (value: unknown, status = 200) => ({ ok: status < 400, status, json: async () => value }) as Response;
const props = { projectId: 'alpha', revisionHash: hash, decisionRef: 'decision_environment_model', optionRef: 'dev_prod' };
const open = () => { render(<ProjectRunCostDelta {...props} />); fireEvent.click(screen.getByRole('button', { name: 'Show run cost' })); };
beforeEach(() => vi.stubGlobal('fetch', vi.fn(async () => reply(evaluated()))));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
describe('Run-cost delta', () => {
  it('fetches only on explicit request', () => {
    render(<ProjectRunCostDelta {...props} />);
    expect(fetch).not.toHaveBeenCalled();
    expect(screen.getByText(/No tenant rate, margin or staffing/)).toBeTruthy();
  });
  it('shows capacities, licences, monitoring storage and the signed delta', async () => {
    open();
    await screen.findByText(/Run cost per month/);
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toBe(`/api/projects/alpha/architecture/run-cost?revision=${hash}&decision=decision_environment_model&option=dev_prod`);
    expect(screen.getAllByText('-US$2,000')).toHaveLength(2);
    expect(screen.getByText('-US$24,000')).toBeTruthy();
    expect(screen.getAllByText('US$70')).toHaveLength(2);
    expect(screen.getByText('Monitoring storage')).toBeTruthy();
  });
  it('formats a EUR result and says when licences are not priced', async () => {
    const eur = (caps: ReturnType<typeof cap>[]) => side(caps, { currency: 'EUR', licences: { ...licences, pro_per_user_month: null, per_month: null } });
    vi.mocked(fetch).mockResolvedValueOnce(reply(evaluated({ currency: 'EUR', comparable: false,
      baseline: eur([cap('p', 'F64', 9000, ['prod'])]), alternative: eur([cap('p', 'F64', 9000, ['prod'])]),
      delta: { per_month: 0, per_year: 0, capacity_per_month: 0, licence_per_month: 0, monitoring_storage_per_month: 0,
        overage_ceiling_per_month: 0, capacities_removed: [], capacities_added: [] } })));
    open();
    await screen.findByText(/Run cost per month/);
    expect(screen.getAllByText('€9,000').length).toBeGreaterThan(0);
    expect(screen.getAllByText('not priced')).toHaveLength(2);
  });
  it('explains a package without declared capacities', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...evaluated(), status: 'not_evaluated', reason: 'architecture_input declares no capacities.' }));
    open();
    await screen.findByText('architecture_input declares no capacities.');
  });
  it('names unpriced positions instead of counting them as zero', async () => {
    const alt = side([cap('p', 'F64', 8000, ['prod'])], { unpriced: [{ item: 'power_bi_licences', reason: 'No EUR list price for Power BI Pro in cost_drivers.yaml.' }] });
    vi.mocked(fetch).mockResolvedValueOnce(reply(evaluated({ comparable: false, alternative: alt })));
    open();
    await screen.findByText('No EUR list price for Power BI Pro in cost_drivers.yaml.');
    expect(screen.getByText(/Not fully comparable/)).toBeTruthy();
  });
  it('rejects a result that could be persisted', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply(evaluated({ persist: true })));
    open();
    await screen.findByText('Run-cost comparison project, revision or option mismatch');
  });
});
