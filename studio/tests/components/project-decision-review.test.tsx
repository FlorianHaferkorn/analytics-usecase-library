import { cleanup, fireEvent, render, screen, waitFor, act } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProjectDecisionReview } from '@/components/project/project-decision-review';
const hash = 'a'.repeat(64), next = 'b'.repeat(64), previewHash = 'c'.repeat(64);
const view = () => ({ project_ref: 'alpha', revision_hash: hash, preview_sha256: previewHash, can_apply: true,
  changes: [{ rule_id: 'rename', decision_ref: 'naming', target: { collection: 'physical_workspaces', entity_id: 'bronze', field: 'name' }, before: 'bronze-old', after: 'bronze-new', rationale: 'Use the explicitly approved name.' }],
  blockers: [], rules: [{ id: 'rename', status: 'ready', reason: 'Explicit approved mapping' }],
});
const reply = (value: unknown, ok = true) => ({ ok, json: async () => value }) as Response;
const application = { project_ref: 'alpha', revision_hash: next, parent_revision_hash: hash, state: 'working', release_required: true, audit_ref: 'architecture/derivations/test.json' };
beforeEach(() => vi.stubGlobal('fetch', vi.fn(async () => reply(view()))));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
async function confirm() {
  await screen.findByText('bronze-old');
  fireEvent.change(screen.getByRole('textbox', { name: 'Review rationale' }), { target: { value: 'Reviewed naming against the approved decision.' } });
  fireEvent.click(screen.getByRole('checkbox'));
}
describe('Architecture decision review', () => {
  it('shows before/after and requires rationale plus exact confirmation', async () => {
    const applied = vi.fn();
    render(<ProjectDecisionReview projectId="alpha" revisionHash={hash} onApplied={applied} />);
    const button = await screen.findByRole('button', { name: 'Update architecture draft' });
    expect((button as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText('bronze-new')).toBeTruthy();
    await confirm();
    vi.mocked(fetch).mockResolvedValueOnce(reply(application));
    fireEvent.click(button);
    await waitFor(() => expect(applied).toHaveBeenCalledWith(application));
    const options = vi.mocked(fetch).mock.calls.at(-1)![1]!;
    expect(JSON.parse(options.body as string)).toEqual({ revisionHash: hash, previewHash: previewHash, rationale: 'Reviewed naming against the approved decision.', confirmed: true });
  });
  it('revokes confirmation when the rationale changes', async () => {
    render(<ProjectDecisionReview projectId="alpha" revisionHash={hash} onApplied={vi.fn()} />);
    await confirm();
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'An amended review requires fresh confirmation.' } });
    expect((screen.getByRole('checkbox') as HTMLInputElement).checked).toBe(false);
  });
  it('shows blockers and never exposes update for an unsafe preview', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...view(), can_apply: false, blockers: ['Conflicting active rules'] }));
    render(<ProjectDecisionReview projectId="alpha" revisionHash={hash} onApplied={vi.fn()} />);
    await screen.findByText('Conflicting active rules');
    expect(screen.queryByRole('button', { name: 'Update architecture draft' })).toBeNull();
  });
  it('rejects a foreign response', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...view(), project_ref: 'beta' }));
    render(<ProjectDecisionReview projectId="alpha" revisionHash={hash} onApplied={vi.fn()} />);
    await screen.findByText('Decision review project or revision mismatch');
    expect(screen.queryByText('bronze-old')).toBeNull();
  });
  it('invalidates a failed update and requires a fresh review', async () => {
    render(<ProjectDecisionReview projectId="alpha" revisionHash={hash} onApplied={vi.fn()} />);
    await confirm();
    vi.mocked(fetch).mockResolvedValueOnce(reply({ error: 'HEAD changed' }, false));
    fireEvent.click(screen.getByRole('button', { name: 'Update architecture draft' }));
    await screen.findByText('HEAD changed');
    expect(screen.queryByRole('checkbox')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Reload decision review' }));
    await screen.findByText('bronze-old');
    expect((screen.getByRole('checkbox') as HTMLInputElement).checked).toBe(false);
  });
  it('does not accept a late update after changing project', async () => {
    let resolve!: (value: Response) => void;
    const applied = vi.fn();
    const { rerender } = render(<ProjectDecisionReview projectId="alpha" revisionHash={hash} onApplied={applied} />);
    await confirm();
    vi.mocked(fetch).mockImplementationOnce(() => new Promise(resolveResponse => { resolve = resolveResponse; }));
    fireEvent.click(screen.getByRole('button', { name: 'Update architecture draft' }));
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...view(), project_ref: 'beta' }));
    rerender(<ProjectDecisionReview projectId="beta" revisionHash={hash} onApplied={applied} />);
    await act(async () => resolve(reply(application)));
    expect(applied).not.toHaveBeenCalled();
  });
  it('explains missing rules without inventing a suggestion or action', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...view(), can_apply: false, changes: [], rules: [] }));
    render(<ProjectDecisionReview projectId="alpha" revisionHash={hash} onApplied={vi.fn()} />);
    await screen.findByText('No decision rules recorded');
    expect(screen.getByRole('link', { name: 'Open Project Package' })).toBeTruthy();
    expect(screen.queryByRole('checkbox')).toBeNull();
  });
});
