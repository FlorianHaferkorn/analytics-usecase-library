import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProjectAlternativeImpact } from '@/components/project/project-alternative-impact';
const hash = 'a'.repeat(64);
const options = [{ decision_ref: 'decision_environment_model', option_ref: 'dev_prod', rule_id: 'environment_lanes_dev_prod' }];
const impact = (patch: Record<string, unknown> = {}) => ({
  schema_version: '1.0.0', project_ref: 'alpha', baseline_revision_hash: hash, decision_ref: 'decision_environment_model',
  baseline_option_ref: 'dev_test_prod', alternative_option_ref: 'dev_prod', status: 'impact_ready', blockers: [],
  impacts: {
    architecture: { environments: { added: [], removed: ['test'], unchanged: ['dev', 'prod'] } },
    plan: { work_packages: { wp_environment_lanes: { before: { role_refs: ['fabric_engineer', 'test_lead'], effort: { value: 6, unit: 'person_days', provenance: 'assumption' } },
      after: { role_refs: ['fabric_engineer'], effort: { value: 4, unit: 'person_days', provenance: 'assumption' } } } },
      tasks: { task_lane_acceptance: { before: ['DEV, TEST and PROD lanes validated'], after: ['DEV and PROD lanes validated'] } } },
    staffing: { role_demand: { added: [], removed: ['test_lead'], unchanged: ['fabric_engineer'] }, effort_totals: { before: { person_days: 6 }, after: { person_days: 4 } }, named_staffing_or_cost_evaluated: false },
    topology: { baseline: [], alternative: [] },
    manifests: { added: [], removed: ['fabric/workspaces/ws_sales_test.request.json', 'fabric/items/pl_sales_test.definition.json'], changed: [] },
    tests: { decision_impact_checks: { before: [], after: [] }, lane_acceptance: { before: {}, after: {} },
      execution_obligations: { added: [], removed: ['workspace_readback:ws_sales_test'], unchanged: [] } },
  },
  obligations: [{ id: 'release_new_input', detail: 'Release the resulting approved revision.' }, { id: 'retire_topology:domain_sales/test', detail: 'Remove or rescope ws_sales_test.' }],
  baseline_unchanged: true, hypothetical: true, approval_granted: false, release_granted: false, tenant_actions_performed: false,
  limitations: ['Hypothetical evaluation of authored rules.'], impact_sha256: 'c'.repeat(64), ...patch,
});
const reply = (value: unknown, ok = true) => ({ ok, json: async () => value }) as Response;
beforeEach(() => vi.stubGlobal('fetch', vi.fn(async () => reply(impact()))));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
describe('Alternative comparison', () => {
  it('does not fetch until an alternative is chosen and states that nothing changes', () => {
    render(<ProjectAlternativeImpact projectId="alpha" revisionHash={hash} options={options} />);
    expect(fetch).not.toHaveBeenCalled();
    expect(screen.getByText(/released baseline stays as it is/)).toBeTruthy();
  });
  it('shows stages, role demand, effort, parts, plan and obligations for the pinned revision', async () => {
    render(<ProjectAlternativeImpact projectId="alpha" revisionHash={hash} options={options} />);
    fireEvent.click(screen.getByRole('button', { name: 'decision environment model → dev prod' }));
    await screen.findByText('− TEST');
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toBe(`/api/projects/alpha/architecture/alternatives?revision=${hash}&decision=decision_environment_model&option=dev_prod`);
    expect(screen.getByText('− test lead')).toBeTruthy();
    expect(screen.getByText('6 person-days → 4 person-days')).toBeTruthy();
    expect(screen.getByText('ws_sales_test')).toBeTruthy();
    expect(screen.getByText('pl_sales_test')).toBeTruthy();
    expect(screen.getByText(/not named staffing or cost/)).toBeTruthy();
    expect(screen.getByText('retire topology · domain_sales/test')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'decision environment model → dev prod' }).getAttribute('aria-pressed')).toBe('true');
  });
  it('shows blockers of a blocked alternative', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply(impact({ status: 'blocked', blockers: ['Environment stage change requires explicitly authored workspace topology for: domain_sales/test'] })));
    render(<ProjectAlternativeImpact projectId="alpha" revisionHash={hash} options={options} />);
    fireEvent.click(screen.getByRole('button', { name: 'decision environment model → dev prod' }));
    await screen.findByText('This alternative is blocked');
  });
  it('rejects a foreign or baseline-changing response', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply(impact({ baseline_unchanged: false })));
    render(<ProjectAlternativeImpact projectId="alpha" revisionHash={hash} options={options} />);
    fireEvent.click(screen.getByRole('button', { name: 'decision environment model → dev prod' }));
    await screen.findByText('Alternative comparison project, revision or option mismatch');
    expect(screen.queryByText('ws_sales_test')).toBeNull();
  });
  it('shows the engine refusal for an unreleased revision', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ error: 'Release blocked: this revision has no explicit release attestation' }, false));
    render(<ProjectAlternativeImpact projectId="alpha" revisionHash={hash} options={options} />);
    fireEvent.click(screen.getByRole('button', { name: 'decision environment model → dev prod' }));
    await screen.findByText(/no explicit release attestation/);
  });
  it('explains when no alternative has a mapping', () => {
    render(<ProjectAlternativeImpact projectId="alpha" revisionHash={hash} options={[]} />);
    expect(screen.getByText('No alternative mapped')).toBeTruthy();
  });
});
