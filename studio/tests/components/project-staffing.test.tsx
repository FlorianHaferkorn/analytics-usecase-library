import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProjectStaffing } from '@/components/project/project-staffing';
const hash = 'a'.repeat(64);
const side = (hours: number) => ({ classes: [{ rate_class: 'engineer_nearshore', hours, weekly_capacity: 30, weeks: hours / 30, earliest_full_team: '2026-10-05',
  people: [{ name: 'Person Alpha', hours: hours * 2 / 3, hours_per_week: 20 }, { name: 'Person Beta', hours: hours / 3, hours_per_week: 10 }] }],
  gaps: [{ rate_class: 'architekt_onshore', hours: 8, detail: 'Nobody on the roster carries this role and location.' }], weeks_in_parallel: hours / 30, people: ['Person Alpha', 'Person Beta'] });
const evaluated = (patch: Record<string, unknown> = {}) => ({ project_ref: 'alpha', baseline_revision_hash: hash, decision_ref: 'decision_environment_model', alternative_option_ref: 'dev_prod',
  status: 'evaluated', personal_data: true, persist: false, baseline: side(30), alternative: side(24),
  delta: { weeks_in_parallel: { before: 1, after: 0.8 }, people_no_longer_needed: [], people_newly_needed: [], new_gaps: [] }, ...patch });
const reply = (value: unknown, status = 200) => ({ ok: status < 400, status, json: async () => value }) as Response;
const props = { projectId: 'alpha', revisionHash: hash, decisionRef: 'decision_environment_model', optionRef: 'dev_prod' };
beforeEach(() => vi.stubGlobal('fetch', vi.fn(async () => reply(evaluated()))));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
describe('Named staffing', () => {
  it('fetches only on explicit request', () => {
    render(<ProjectStaffing {...props} />);
    expect(fetch).not.toHaveBeenCalled();
    expect(screen.getByText(/never stored or exported/)).toBeTruthy();
  });
  it('shows people, hours, weeks and the uncovered role', async () => {
    render(<ProjectStaffing {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show named staffing' }));
    await screen.findByText(/Named staffing · alternative \(1 → 0.8 weeks in parallel\)/);
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toBe(`/api/projects/alpha/architecture/commercial/staffing?revision=${hash}&decision=decision_environment_model&option=dev_prod`);
    expect(screen.getByText('Person Alpha (16 h), Person Beta (8 h)')).toBeTruthy();
    expect(screen.getByText('architekt onshore')).toBeTruthy();
  });
  it('tells a non-admin why no names are shown', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ error: 'denied' }, 403));
    render(<ProjectStaffing {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show named staffing' }));
    await screen.findByText('Only project admins can see named staffing.');
  });
  it('shows roster findings instead of names', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply(evaluated({ status: 'findings', personal_data: false, findings: ['Row 2: hours per week must be between 1 and 60'], baseline: undefined, alternative: undefined, delta: undefined })));
    render(<ProjectStaffing {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show named staffing' }));
    await screen.findByText('Row 2: hours per week must be between 1 and 60');
  });
  it('rejects a result that could be persisted', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply(evaluated({ persist: true })));
    render(<ProjectStaffing {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show named staffing' }));
    await screen.findByText('Staffing project, revision or option mismatch');
  });
});
