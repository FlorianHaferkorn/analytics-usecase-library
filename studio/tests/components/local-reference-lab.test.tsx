import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { LocalReferenceLab } from '@/components/project/local-reference-lab';
vi.mock('@/components/canvas/custom-canvas', () => ({ CustomCanvas: () => <div>Reference graph</div> }));
const report = () => ({ schema_version: '1.0.0', reference_id: 'fixture', run_id: 'a'.repeat(64), variant: 'dev_test_prod', project_ref: 'local_reference', revision_hash: 'b'.repeat(64), source_kind: 'synthetic', evidence_kind: 'local_check', tenant_actions_performed: false, live_apply_allowed: false,
  stages: [{ id: 'input', title: 'Synthetic input', status: 'passed', evidence_kind: 'local_check', summary: 'Explicit fixture input' }], checks: [{ id: 'simulation', title: 'Fake target', status: 'passed', evidence_kind: 'simulation', detail: 'Never a real tenant' }], graph: { nodes: [], edges: [] }, files: [{ path: 'docs/reference.md', content: '# Synthetic documentation', sha256: 'c'.repeat(64) }], limitations: ['Engine compatibility requires a tenant test.'] });
const reply = (value: unknown, ok = true) => ({ ok, json: async () => value }) as Response;
beforeEach(() => vi.stubGlobal('fetch', vi.fn(async () => reply(report()))));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
async function run() { fireEvent.click(screen.getByRole('checkbox')); fireEvent.click(screen.getByRole('button', { name: 'Run local reference' })); }
describe('Local reference lab', () => {
  it('never runs on mount and requires a synthetic confirmation', async () => {
    render(<LocalReferenceLab />); expect(fetch).not.toHaveBeenCalled();
    expect((screen.getByRole('button', { name: 'Run local reference' }) as HTMLButtonElement).disabled).toBe(true);
    await run(); await screen.findByText('Explicit fixture input');
    expect(JSON.parse(vi.mocked(fetch).mock.calls[0][1]!.body as string)).toEqual({ variant: 'dev_test_prod', confirmSynthetic: true });
    expect((screen.getByRole('checkbox') as HTMLInputElement).checked).toBe(false);
  });
  it('exposes evidence, real output content and the shared architecture renderer', async () => {
    render(<LocalReferenceLab />); await run(); await screen.findByText('Explicit fixture input');
    fireEvent.click(screen.getByRole('button', { name: 'Checks & limitations' }));
    fireEvent.click(screen.getByText('Fake target')); expect(screen.getByText('Never a real tenant')).toBeTruthy();
    expect(screen.getByText('Engine compatibility requires a tenant test.')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Generated files' })); expect(screen.getByText('# Synthetic documentation')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Architecture' })); expect(screen.getByText('Reference graph')).toBeTruthy();
  });
  it('invalidates previous outputs when the decision changes', async () => {
    render(<LocalReferenceLab />); await run(); await screen.findByText('Explicit fixture input');
    fireEvent.change(screen.getByRole('combobox', { name: 'Reference environment decision' }), { target: { value: 'dev_prod' } });
    expect(screen.queryByText('Explicit fixture input')).toBeNull(); expect(screen.queryByRole('button', { name: 'Download reference ZIP' })).toBeNull();
    expect(fetch).toHaveBeenCalledTimes(1); expect((screen.getByRole('checkbox') as HTMLInputElement).checked).toBe(false);
  });
  it.each([{ project_ref: 'customer' }, { variant: 'dev_prod' }, { live_apply_allowed: true }, { tenant_actions_performed: true }, { stages: [{ evidence_kind: 'tenant_verified' }] }])('rejects foreign or false evidence %o', async changed => {
    vi.mocked(fetch).mockResolvedValue(reply({ ...report(), ...changed })); render(<LocalReferenceLab />); await run();
    await screen.findByRole('alert'); expect(screen.queryByRole('button', { name: 'Download reference ZIP' })).toBeNull();
  });
  it('disables controls while running and does not hide a failure', async () => {
    let resolve!: (value: Response) => void;
    vi.mocked(fetch).mockImplementationOnce(() => new Promise(done => { resolve = done; }));
    render(<LocalReferenceLab />); await run();
    expect((screen.getByRole('combobox') as HTMLSelectElement).disabled).toBe(true);
    resolve(reply({ error: 'Local runtime unavailable' }, false));
    await screen.findByText('Local runtime unavailable'); await waitFor(() => expect((screen.getByRole('combobox') as HTMLSelectElement).disabled).toBe(false));
  });
});
