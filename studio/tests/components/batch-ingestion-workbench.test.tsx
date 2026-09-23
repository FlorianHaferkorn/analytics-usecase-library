import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { BatchIngestionEditor, exampleBatchContract } from '@/components/project/batch-ingestion-workbench';

const selection = vi.hoisted(() => ({ projectId: 'project_demo', packageRevisionHash: 'a'.repeat(64) }));
vi.mock('@/lib/store/project-store', () => ({ useProjectStore: Object.assign(vi.fn(), { getState: () => selection }) }));
vi.mock('@/components/project/use-pinned-project', () => ({ usePinnedProject: vi.fn() }));
vi.mock('@/components/canvas/custom-canvas', () => ({ CustomCanvas: () => <div>Batch graph</div> }));

const revision = 'a'.repeat(64);
const view = () => ({ valid: true, contract_hash: 'c'.repeat(64), blockers: [], names: { table: 'bronze.orders' }, impact: [{ id: 'load', title: 'Load consequences', detail: 'Inclusive source-version boundary.' }], graph: { nodes: [], edges: [] }, limitations: ['No tenant runtime was contacted.'] });
const inspection = (saved = false) => ({ project_ref: 'project_demo', revision_hash: revision, is_current_revision: true, contract: saved ? structuredClone(exampleBatchContract) : null, view: saved ? view() : null, tenant_actions_performed: false });
const preview = () => ({ project_ref: 'project_demo', revision_hash: revision, preview_hash: 'b'.repeat(64), can_save: true, blockers: [], changes: [{ path: 'contract', before: null, after: exampleBatchContract }], view: view(), release_required: true, tenant_actions_performed: false });
const saved = () => ({ project_ref: 'project_demo', revision_hash: 'd'.repeat(64), parent_revision_hash: revision, state: 'working', release_required: true, tenant_actions_performed: false });
const reply = (value: unknown, ok = true) => ({ ok, json: async () => value }) as Response;
const posts = () => vi.mocked(fetch).mock.calls.filter(([, options]) => options?.method === 'POST');
const lastBody = () => JSON.parse(posts().at(-1)![1]!.body as string);
const saveButton = () => screen.getByRole('button', { name: 'Save Working version' }) as HTMLButtonElement;
const reviewConfirmation = () => screen.getByRole('checkbox', { name: /I reviewed these changes/ });

beforeEach(() => {
  selection.projectId = 'project_demo'; selection.packageRevisionHash = revision;
  vi.stubGlobal('fetch', vi.fn(async () => reply(inspection())));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.clearAllMocks(); });

async function open(savedContract = false, onSaved = vi.fn()) {
  vi.mocked(fetch).mockResolvedValueOnce(reply(inspection(savedContract)));
  render(<BatchIngestionEditor projectId="project_demo" revision={revision} onSaved={onSaved} />);
  await waitFor(() => expect((screen.getByRole('group', { name: 'Batch ingestion contract' }) as HTMLFieldSetElement).disabled).toBe(false));
  return onSaved;
}
async function review(value = preview()) {
  vi.mocked(fetch).mockResolvedValueOnce(reply(value));
  fireEvent.click(screen.getByRole('button', { name: 'Review impact' }));
  await screen.findByText('Save a new Working version');
}

describe('Batch ingestion workbench boundaries', () => {
  it('loads only a pinned inspection on mount, without autosave, release or tenant calls', async () => {
    await open();
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(vi.mocked(fetch).mock.calls[0][0]).toBe(`/api/projects/project_demo/ingestion?revision=${revision}`);
    expect(posts()).toHaveLength(0);
    fireEvent.change(screen.getByLabelText('Domain'), { target: { value: 'finance' } });
    expect(posts()).toHaveLength(0);
  });

  it('preserves comma editing and sends distinct business keys in the preview', async () => {
    await open();
    const keys = screen.getByLabelText('Business keys (comma-separated)') as HTMLInputElement;
    fireEvent.change(keys, { target: { value: 'order_id, ' } });
    expect(keys.value).toBe('order_id, ');
    fireEvent.change(keys, { target: { value: 'order_id, country_id' } });
    await review();
    expect(lastBody()).toEqual({ mode: 'preview', revisionHash: revision, contract: { ...exampleBatchContract, keys: ['order_id', 'country_id'] } });
    expect(posts()).toHaveLength(1);
    expect(screen.getByText('Batch graph')).toBeTruthy();
  });

  it('requires an exact reviewed preview, sufficient rationale and explicit confirmation before saving', async () => {
    const onSaved = await open(); await review();
    expect(saveButton().disabled).toBe(true);
    fireEvent.click(reviewConfirmation());
    expect(saveButton().disabled).toBe(true);
    fireEvent.change(screen.getByLabelText('Review rationale'), { target: { value: 'Reviewed naming, columns and incremental recovery behavior.' } });
    expect((reviewConfirmation() as HTMLInputElement).checked).toBe(false);
    fireEvent.click(reviewConfirmation());
    expect(saveButton().disabled).toBe(false);
    vi.mocked(fetch).mockResolvedValueOnce(reply(saved()));
    fireEvent.click(saveButton());
    await waitFor(() => expect(onSaved).toHaveBeenCalledWith(saved()));
    expect(lastBody()).toEqual({ mode: 'save', revisionHash: revision, contract: exampleBatchContract, previewHash: 'b'.repeat(64), rationale: 'Reviewed naming, columns and incremental recovery behavior.', confirmed: true });
    expect(posts()).toHaveLength(2);
    expect(posts().every(([url]) => url === '/api/projects/project_demo/ingestion')).toBe(true);
  });

  it('invalidates the reviewed preview and confirmation after any contract edit', async () => {
    await open(); await review();
    fireEvent.change(screen.getByLabelText('Review rationale'), { target: { value: 'Reviewed the exact versioned input contract.' } });
    fireEvent.click(reviewConfirmation());
    fireEvent.click(screen.getByRole('button', { name: '1 · Inputs' }));
    fireEvent.change(screen.getByLabelText('Target table'), { target: { value: 'other_orders' } });
    fireEvent.click(screen.getByRole('button', { name: '2 · Review changes' }));
    expect(screen.getByText('Review required')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Save Working version' })).toBeNull();
    expect(posts()).toHaveLength(1);
  });

  it('does not execute unsaved inputs or offer export of an unsaved draft', async () => {
    await open();
    fireEvent.click(screen.getByRole('button', { name: '3 · Local test' }));
    expect(screen.getByText(/Unsaved inputs are not executed/)).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Run local batches' })).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: '4 · Outputs' }));
    expect((screen.getByRole('button', { name: 'Download released batch ZIP' }) as HTMLButtonElement).disabled).toBe(true);
    expect(posts()).toHaveLength(0);
  });

  it('runs only explicit rows against the saved version, with separate confirmation and evidence', async () => {
    await open(true);
    fireEvent.click(screen.getByRole('button', { name: '3 · Local test' }));
    const button = screen.getByRole('button', { name: 'Run local batches' }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    fireEvent.click(screen.getByRole('button', { name: 'Use synthetic orders example' }));
    fireEvent.click(screen.getByRole('checkbox', { name: /Run only these local test rows/ }));
    vi.mocked(fetch).mockResolvedValueOnce(reply({ project_ref: 'project_demo', revision_hash: revision, contract_hash: 'c'.repeat(64), evidence_kind: 'local_check', tenant_actions_performed: false, batches: [{ counts: { inserted: 1 }, watermark: 2, replayed: false }], limitations: ['Only supplied rows were tested.'] }));
    fireEvent.click(button);
    await screen.findByText('Only supplied rows were tested.');
    expect(lastBody().mode).toBe('test');
    expect(lastBody().revisionHash).toBe(revision);
    expect(lastBody().confirmed).toBe(true);
    expect(lastBody()).not.toHaveProperty('contract');
    expect(lastBody()).not.toHaveProperty('state');
    expect(posts()).toHaveLength(1);
  });

  it.each([{ project_ref: 'foreign' }, { revision_hash: 'e'.repeat(64) }])('rejects a foreign preview %o', async changed => {
    await open();
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...preview(), ...changed }));
    fireEvent.click(screen.getByRole('button', { name: 'Review impact' }));
    await screen.findByRole('alert');
    expect(screen.queryByRole('button', { name: 'Save Working version' })).toBeNull();
  });

  it('rejects a foreign saved response and never updates the selected version', async () => {
    const onSaved = await open(); await review();
    fireEvent.change(screen.getByLabelText('Review rationale'), { target: { value: 'Reviewed the exact versioned input contract.' } });
    fireEvent.click(reviewConfirmation());
    vi.mocked(fetch).mockResolvedValueOnce(reply({ ...saved(), parent_revision_hash: 'f'.repeat(64) }));
    fireEvent.click(saveButton());
    await screen.findByRole('alert'); expect(onSaved).not.toHaveBeenCalled();
    expect(selection.packageRevisionHash).toBe(revision);
  });

  it('refuses actions after the globally selected project changes', async () => {
    await open(); selection.projectId = 'other_project';
    fireEvent.click(screen.getByRole('button', { name: 'Review impact' }));
    expect(posts()).toHaveLength(0);
  });
});
