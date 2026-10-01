import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProjectRunCostDelta } from '@/components/project/project-run-cost-delta';
const hash = 'a'.repeat(64);
const cap = (id: string, sku: string, usd: number, environments: string[]) => ({ capacity_id: id, sku, billing: 'payg', environments,
  usd_per_month: usd, overage: { enabled: false, threshold_source: 'customer', max_usd_per_month: 0 } });
const licences = { authors: 5, viewers: 200, production_sku: 'F64', viewers_need_pro: false, pro_users: 5, pro_usd_per_user_month: 14,
  usd_per_month: 70, basis: 'production SKU F64 or larger: viewers without licence' };
const side = (caps: ReturnType<typeof cap>[]) => {
  const capacity = caps.reduce((sum, row) => sum + row.usd_per_month, 0);
  return { capacities: caps, capacity_usd_per_month: capacity, licences, usd_per_month: capacity + 70,
    overage_ceiling_usd_per_month: 0, priced_capacities: caps.length, unpriced: [] as Array<{ capacity_id: string; reason: string }> };
};
const evaluated = (patch: Record<string, unknown> = {}) => ({ project_ref: 'alpha', baseline_revision_hash: hash, decision_ref: 'decision_environment_model',
  alternative_option_ref: 'dev_prod', status: 'evaluated', persist: false, currency: 'USD', price_basis: 'Microsoft list price',
  price_valid_from: '2025-02-01', comparable: true,
  baseline: side([cap('p', 'F64', 8000, ['prod']), cap('t', 'F16', 2000, ['test'])]),
  alternative: side([cap('p', 'F64', 8000, ['prod'])]),
  delta: { usd_per_month: -2000, usd_per_year: -24000, capacity_usd_per_month: -2000, licence_usd_per_month: 0,
    overage_ceiling_usd_per_month: 0, capacities_removed: ['t'], capacities_added: [] }, ...patch });
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
  it('shows capacities, licences and the signed delta', async () => {
    open();
    await screen.findByText(/Run cost per month/);
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toBe(`/api/projects/alpha/architecture/run-cost?revision=${hash}&decision=decision_environment_model&option=dev_prod`);
    expect(screen.getAllByText('-$2,000')).toHaveLength(2);
    expect(screen.getByText('-$24,000')).toBeTruthy();
    expect(screen.getAllByText('$70')).toHaveLength(2);
  });
  it('explains a package without declared capacities', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...evaluated(), status: 'not_evaluated', reason: 'architecture_input declares no capacities.' }));
    open();
    await screen.findByText('architecture_input declares no capacities.');
  });
  it('names unpriced capacities instead of counting them as zero', async () => {
    const alt = side([cap('p', 'F64', 8000, ['prod'])]);
    alt.unpriced = [{ capacity_id: 'x', reason: 'No list price for F8192 in cost_drivers.yaml.' }];
    vi.mocked(fetch).mockResolvedValueOnce(reply(evaluated({ comparable: false, alternative: alt })));
    open();
    await screen.findByText('No list price for F8192 in cost_drivers.yaml.');
    expect(screen.getByText(/Not fully comparable/)).toBeTruthy();
  });
  it('rejects a result that could be persisted', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply(evaluated({ persist: true })));
    open();
    await screen.findByText('Run-cost comparison project, revision or option mismatch');
  });
});
