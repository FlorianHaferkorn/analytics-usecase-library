import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProjectCommercialImpact } from '@/components/project/project-commercial-impact';
const hash = 'a'.repeat(64);
const side = (tester: number, parallel: number, gaps: Array<{ id: string; detail: string }>) => ({ packages: [], hours_by_canon_role: { architekt: 8, engineer: 30 - (9 - tester), tester }, window_workdays: { parallel, serial: parallel + 6 }, capacity_notes: [], gaps });
const evaluated = (patch: Record<string, unknown> = {}) => ({ project_ref: 'alpha', baseline_revision_hash: hash, decision_ref: 'decision_environment_model', alternative_option_ref: 'dev_prod',
  status: 'evaluated', price_values_embedded: false,
  baseline: side(9, 8, []), alternative: side(6, 7, [{ id: 'canon_role_without_plan_demand:tester', detail: 'The canon packages need 6 h of tester, but no plan role that maps to it is demanded.' }]),
  delta: { hours_by_canon_role: {}, window_workdays: { before: { parallel: 8, serial: 14 }, after: { parallel: 7, serial: 13 } }, new_gaps: ['canon_role_without_plan_demand:tester'], resolved_gaps: [] },
  proposal_assumptions_markdown: '## Proposal assumptions (dev prod)\n- Delivery band: 5–7 workdays\n', ...patch });
const reply = (value: unknown, ok = true) => ({ ok, json: async () => value }) as Response;
const props = { projectId: 'alpha', revisionHash: hash, decisionRef: 'decision_environment_model', optionRef: 'dev_prod' };
beforeEach(() => vi.stubGlobal('fetch', vi.fn(async () => reply(evaluated()))));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
describe('Commercial comparison', () => {
  it('fetches only on explicit request and states that no price is shown', () => {
    render(<ProjectCommercialImpact {...props} />);
    expect(fetch).not.toHaveBeenCalled();
    expect(screen.getByText(/No rate, price or margin is shown/)).toBeTruthy();
  });
  it('shows hours per canon role, window, new open points and rate-free assumptions', async () => {
    render(<ProjectCommercialImpact {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Evaluate against price canon' }));
    await screen.findByText('Hours per canon role · accepted baseline → alternative');
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toBe(`/api/projects/alpha/architecture/commercial?revision=${hash}&decision=decision_environment_model&option=dev_prod`);
    expect(screen.getByText('9 h')).toBeTruthy();
    expect(screen.getByText('6 h')).toBeTruthy();
    expect(screen.getByText('8 → 7 workdays')).toBeTruthy();
    expect(screen.getByText('New · canon role without plan demand')).toBeTruthy();
    expect(screen.getByText(/Delivery band: 5–7 workdays/)).toBeTruthy();
  });
  it('explains an unconfigured price canon instead of showing zero', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...evaluated(), status: 'not_checked', reason: 'Mandant nagarro: keine Werte geladen.', baseline: undefined, alternative: undefined, delta: undefined }));
    render(<ProjectCommercialImpact {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Evaluate against price canon' }));
    await screen.findByText('Price canon not configured');
    expect(screen.queryByText('0 h')).toBeNull();
  });
  it('lists tenant findings', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...evaluated(), status: 'tenant_findings', findings: ['3 Platzhalter unbefuellt'] }));
    render(<ProjectCommercialImpact {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Evaluate against price canon' }));
    await screen.findByText('3 Platzhalter unbefuellt');
  });
  it('rejects a result that does not declare price_values_embedded false', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply(evaluated({ price_values_embedded: true })));
    render(<ProjectCommercialImpact {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Evaluate against price canon' }));
    await screen.findByText('Commercial comparison project, revision or option mismatch');
  });
});
