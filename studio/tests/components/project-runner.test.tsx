import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProjectRunner } from '@/components/project/project-runner';
import type { DeploymentPlan } from '@/lib/bridge/project-deployment';

const selected = vi.hoisted(() => ({ projectId: 'alpha', packageRevisionHash: 'a'.repeat(64) }));
vi.mock('@/lib/store/project-store', () => ({ useProjectStore: { getState: () => selected } }));
const hash = 'a'.repeat(64), approvalId = 'b'.repeat(64), planHash = 'c'.repeat(64);
const plan: DeploymentPlan = { project_ref: 'alpha', revision_hash: hash, tenant_id: 'tenant-id', principal_id: 'principal-id', environment: 'dev', plan_sha256: planHash, workspace_apply_ready: true, whole_project_apply_ready: false, operations: [], capabilities: [] };
const status = { project_ref: 'alpha', enabled: true, can_approve: true, can_execute: true, identity_broker_available: true, environments: ['dev'], actor: 'github:123', independent_execution_environments: [], limitations: [] };
const receipt = { project_ref: 'alpha', revision_hash: hash, approval_id: approvalId, plan_sha256: planHash, expires_at: new Date(Date.now() + 900000).toISOString(), approved_by: 'github:123', status: 'approved_not_executed' };
const reply = (value: unknown, ok = true) => ({ ok, json: async () => value }) as Response;
beforeEach(() => { selected.projectId = 'alpha'; selected.packageRevisionHash = hash; vi.stubGlobal('fetch', vi.fn(async () => reply(status))); });
afterEach(() => { cleanup(); vi.unstubAllGlobals(); window.history.replaceState(null, '', '/'); });
async function approve() {
  await screen.findByRole('button', { name: 'Save workspace approval' });
  fireEvent.change(screen.getByRole('textbox', { name: 'Workspace approval rationale' }), { target: { value: 'Reviewed this exact tenant workspace plan.' } });
  fireEvent.click(screen.getByRole('checkbox', { name: /I approve the exact/ }));
  vi.mocked(fetch).mockResolvedValueOnce(reply(receipt));
  fireEvent.click(screen.getByRole('button', { name: 'Save workspace approval' }));
  await screen.findByRole('button', { name: 'Execute approved workspace plan' });
}
describe('Protected workspace execution UI', () => {
  it('keeps self-approved team execution disabled even when both allowlists include the operator', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...status, independent_execution_environments: ['dev'] }));
    render(<ProjectRunner projectId="alpha" revision={hash} plan={plan} />);
    await approve();
    fireEvent.click(screen.getByRole('checkbox', { name: /Create the listed workspaces/ }));
    expect(screen.getByText(/Your approval cannot be executed from this account/)).toBeTruthy();
    expect((screen.getByRole('button', { name: 'Execute approved workspace plan' }) as HTMLButtonElement).disabled).toBe(true);
  });
  it('allows a different authorized operator to execute a retrieved team approval', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...status, can_approve: false, actor: 'github:456', independent_execution_environments: ['dev'] }));
    render(<ProjectRunner projectId="alpha" revision={hash} plan={plan} />);
    await screen.findByText(/Host policy is enabled/);
    fireEvent.change(screen.getByRole('textbox', { name: 'Saved approval ID' }), { target: { value: approvalId } });
    vi.mocked(fetch).mockResolvedValueOnce(reply({ status: 'approved_not_executed', receipt }));
    fireEvent.click(screen.getByRole('button', { name: 'Retrieve saved outcome' }));
    await screen.findByRole('button', { name: 'Execute approved workspace plan' });
    fireEvent.click(screen.getByRole('checkbox', { name: /Create the listed workspaces/ }));
    expect((screen.getByRole('button', { name: 'Execute approved workspace plan' }) as HTMLButtonElement).disabled).toBe(false);
  });
  it('fails closed when a team approval has no recorded approver identity', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...status, actor: 'github:456', independent_execution_environments: ['dev'] }));
    render(<ProjectRunner projectId="alpha" revision={hash} plan={plan} />);
    await screen.findByText(/Host policy is enabled/);
    fireEvent.change(screen.getByRole('textbox', { name: 'Saved approval ID' }), { target: { value: approvalId } });
    vi.mocked(fetch).mockResolvedValueOnce(reply({ status: 'approved_not_executed', receipt: { ...receipt, approved_by: undefined } }));
    fireEvent.click(screen.getByRole('button', { name: 'Retrieve saved outcome' }));
    await screen.findByRole('button', { name: 'Execute approved workspace plan' });
    fireEvent.click(screen.getByRole('checkbox', { name: /Create the listed workspaces/ }));
    expect(screen.getByText(/identities are not available for verification/)).toBeTruthy();
    expect((screen.getByRole('button', { name: 'Execute approved workspace plan' }) as HTMLButtonElement).disabled).toBe(true);
  });
  it('allows approval-only actors to approve without execution membership', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...status, can_execute: false, checks: [{ id: 'executor', title: 'Execution operator', state: 'missing', detail: 'Not assigned', action: 'Use a separate authorized executor.' }] }));
    render(<ProjectRunner projectId="alpha" revision={hash} plan={plan} />);
    await approve();
    fireEvent.click(screen.getByRole('checkbox', { name: /Create the listed workspaces/ }));
    expect((screen.getByRole('button', { name: 'Execute approved workspace plan' }) as HTMLButtonElement).disabled).toBe(true);
  });
  it('allows execution-only actors to use a saved approval without granting approval authority', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...status, can_approve: false, checks: [{ id: 'approver', title: 'Approval operator', state: 'missing', detail: 'Not assigned', action: 'Use a separate authorized approver.' }] }));
    render(<ProjectRunner projectId="alpha" revision={hash} plan={plan} />);
    await screen.findByText(/Host policy is enabled/);
    expect(screen.queryByRole('button', { name: 'Save workspace approval' })).toBeNull();
    fireEvent.change(screen.getByRole('textbox', { name: 'Saved approval ID' }), { target: { value: approvalId } });
    vi.mocked(fetch).mockResolvedValueOnce(reply({ status: 'approved_not_executed', receipt }));
    fireEvent.click(screen.getByRole('button', { name: 'Retrieve saved outcome' }));
    await screen.findByRole('button', { name: 'Execute approved workspace plan' });
    fireEvent.click(screen.getByRole('checkbox', { name: /Create the listed workspaces/ }));
    expect((screen.getByRole('button', { name: 'Execute approved workspace plan' }) as HTMLButtonElement).disabled).toBe(false);
  });
  it('does not expose mutation controls for a disabled host', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...status, enabled: false }));
    render(<ProjectRunner projectId="alpha" revision={hash} plan={plan} />);
    await screen.findByText(/Live execution is disabled/);
    expect(screen.queryByRole('button', { name: 'Save workspace approval' })).toBeNull();
  });
  it('requires separate explicit approval and execution confirmations', async () => {
    render(<ProjectRunner projectId="alpha" revision={hash} plan={plan} />);
    await approve();
    const execute = screen.getByRole('button', { name: 'Execute approved workspace plan' });
    expect(screen.queryByText('Tenant verified · workspace readback only')).toBeNull();
    expect((execute as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole('checkbox', { name: /Create the listed workspaces/ }));
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...receipt, outcome: { status: 'workspace_verified' } }));
    fireEvent.click(execute);
    await screen.findByText(/Workspace readback verified/);
    expect(screen.getByText('Tenant verified · workspace readback only')).toBeTruthy();
    expect(JSON.parse(vi.mocked(fetch).mock.calls.at(-1)![1]!.body as string)).toEqual({ mode: 'execute', revisionHash: hash, approvalId, confirmed: true });
    expect(screen.queryByRole('button', { name: 'Execute approved workspace plan' })).toBeNull();
  });
  it('never retries an uncertain execution and allows evidence retrieval', async () => {
    render(<ProjectRunner projectId="alpha" revision={hash} plan={plan} />);
    await approve();
    fireEvent.click(screen.getByRole('checkbox', { name: /Create the listed workspaces/ }));
    vi.mocked(fetch).mockResolvedValueOnce(reply({ error: 'Outcome uncertain' }, false));
    fireEvent.click(screen.getByRole('button', { name: 'Execute approved workspace plan' }));
    await screen.findByText('Outcome uncertain');
    expect(screen.queryByRole('button', { name: 'Execute approved workspace plan' })).toBeNull();
    vi.mocked(fetch).mockResolvedValueOnce(reply({ status: 'consumed_requires_reconciliation', receipt }));
    fireEvent.click(screen.getByRole('button', { name: 'Retrieve saved outcome' }));
    await screen.findByText(/Saved attempt state: consumed requires reconciliation/);
    expect(vi.mocked(fetch).mock.calls.filter(([, init]) => init?.method === 'POST')).toHaveLength(2);
  });
  it('does not allow restored approval to execute a different plan', async () => {
    render(<ProjectRunner projectId="alpha" revision={hash} plan={{ ...plan, plan_sha256: hash }} />);
    await screen.findByText(/Host policy is enabled/);
    fireEvent.change(screen.getByRole('textbox', { name: 'Saved approval ID' }), { target: { value: approvalId } });
    vi.mocked(fetch).mockResolvedValueOnce(reply({ status: 'approved_not_executed', receipt }));
    fireEvent.click(screen.getByRole('button', { name: 'Retrieve saved outcome' }));
    await screen.findByText(/Build and review the matching workspace plan/);
    expect(screen.queryByRole('button', { name: 'Execute approved workspace plan' })).toBeNull();
  });
  it('blocks expired approvals', async () => {
    render(<ProjectRunner projectId="alpha" revision={hash} plan={plan} />);
    await screen.findByText(/Host policy is enabled/);
    fireEvent.change(screen.getByRole('textbox', { name: 'Saved approval ID' }), { target: { value: approvalId } });
    vi.mocked(fetch).mockResolvedValueOnce(reply({ status: 'expired', receipt: { ...receipt, expires_at: '2020-01-01T00:00:00Z' } }));
    fireEvent.click(screen.getByRole('button', { name: 'Retrieve saved outcome' }));
    await screen.findByText(/Saved attempt state: expired/);
    expect(screen.queryByRole('button', { name: 'Execute approved workspace plan' })).toBeNull();
  });
  it('drops a late approval result after synchronous project change', async () => {
    render(<ProjectRunner projectId="alpha" revision={hash} plan={plan} />);
    await screen.findByRole('button', { name: 'Save workspace approval' });
    fireEvent.change(screen.getByRole('textbox', { name: 'Workspace approval rationale' }), { target: { value: 'Reviewed this exact tenant workspace plan.' } });
    fireEvent.click(screen.getByRole('checkbox', { name: /I approve the exact/ }));
    let done!: (value: Response) => void;
    vi.mocked(fetch).mockImplementationOnce(() => new Promise(resolve => { done = resolve; }));
    fireEvent.click(screen.getByRole('button', { name: 'Save workspace approval' }));
    selected.projectId = 'beta';
    await act(async () => done(reply(receipt)));
    expect(screen.queryByRole('button', { name: 'Execute approved workspace plan' })).toBeNull();
  });
  it('invalidates approval and consent on plan change without remounting inputs', async () => {
    const view = render(<ProjectRunner projectId="alpha" revision={hash} plan={plan}><input aria-label="Planning input" /></ProjectRunner>);
    await approve();
    const input = screen.getByRole('textbox', { name: 'Planning input' }); input.focus();
    view.rerender(<ProjectRunner projectId="alpha" revision={hash} plan={{ ...plan, plan_sha256: 'd'.repeat(64) }}><input aria-label="Planning input" /></ProjectRunner>);
    expect(screen.queryByRole('button', { name: 'Execute approved workspace plan' })).toBeNull();
    expect(document.activeElement).toBe(input);
    expect((screen.getByRole('checkbox', { name: /I approve the exact/ }) as HTMLInputElement).checked).toBe(false);
  });
  it('discards a late approval response after a plan changes within the same version', async () => {
    const view = render(<ProjectRunner projectId="alpha" revision={hash} plan={plan} />);
    await screen.findByRole('button', { name: 'Save workspace approval' });
    fireEvent.change(screen.getByRole('textbox', { name: 'Workspace approval rationale' }), { target: { value: 'Reviewed this exact tenant workspace plan.' } });
    fireEvent.click(screen.getByRole('checkbox', { name: /I approve the exact/ }));
    let done!: (value: Response) => void;
    vi.mocked(fetch).mockImplementationOnce(() => new Promise(resolve => { done = resolve; }));
    fireEvent.click(screen.getByRole('button', { name: 'Save workspace approval' }));
    view.rerender(<ProjectRunner projectId="alpha" revision={hash} plan={{ ...plan, plan_sha256: 'd'.repeat(64) }} />);
    await act(async () => done(reply(receipt)));
    expect(screen.queryByRole('button', { name: 'Execute approved workspace plan' })).toBeNull();
    expect(new URL(window.location.href).searchParams.has('runner_approval')).toBe(false);
  });
  it('shows OAuth access errors without a mutation fallback', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(reply({ error: { message: 'OAuth required' } }, false));
    render(<ProjectRunner projectId="alpha" revision={hash} plan={plan} />);
    await waitFor(() => expect(screen.getByRole('alert').textContent).toBe('OAuth required'));
    expect(screen.queryByRole('button', { name: 'Save workspace approval' })).toBeNull();
  });
  it('retains only scoped recovery identifiers across a reload, never execution consent', async () => {
    const first = render(<ProjectRunner projectId="alpha" revision={hash} plan={plan} />);
    await approve();
    const url = new URL(window.location.href);
    expect(url.searchParams.get('runner_approval')).toBe(approvalId);
    expect(url.searchParams.get('runner_project')).toBe('alpha');
    expect(url.searchParams.get('runner_revision')).toBe(hash);
    expect(url.searchParams.has('plan')).toBe(false);
    first.unmount();
    render(<ProjectRunner projectId="alpha" revision={hash} plan={plan} />);
    await screen.findByText(/Host policy is enabled/);
    expect((screen.getByRole('textbox', { name: 'Saved approval ID' }) as HTMLInputElement).value).toBe(approvalId);
    expect(screen.queryByRole('button', { name: 'Execute approved workspace plan' })).toBeNull();
  });
  it('does not carry a recovery identifier into another project', async () => {
    window.history.replaceState(null, '', `/?runner_project=beta&runner_revision=${hash}&runner_approval=${approvalId}`);
    render(<ProjectRunner projectId="alpha" revision={hash} plan={plan} />);
    await screen.findByText(/Host policy is enabled/);
    expect((screen.getByRole('textbox', { name: 'Saved approval ID' }) as HTMLInputElement).value).toBe('');
  });
});
