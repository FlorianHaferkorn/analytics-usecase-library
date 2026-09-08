import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { emptyDiscovery } from '@/lib/discovery/document';
const h = vi.hoisted(() => ({ state: { projectId: 'a', projectName: 'Project A' } }));
vi.mock('@/lib/store/project-store', () => ({ useProjectStore: (selector: (state: typeof h.state) => unknown) => selector(h.state) }));
vi.mock('@/components/discovery/source-panel', () => ({ SourcePanel: ({ sources, onAddSource, readOnly }: { sources: { name: string }[]; onAddSource: (source: unknown) => void; readOnly: boolean }) => <div>{sources.map((source) => <p key={source.name}>{source.name}</p>)}<button disabled={readOnly} onClick={() => onAddSource({ id: 's1', name: `Evidence ${h.state.projectId}`, type: 'text', content: 'Only this project', addedAt: '2026-09-07T10:00:00Z' })}>Add evidence</button></div> }));
vi.mock('@/components/discovery/discovery-chat', () => ({ DiscoveryChat: () => <p>Discovery Chat</p> }));
import { DiscoveryClient } from '@/app/(studio)/discovery/discovery-client';
beforeEach(() => { h.state = { projectId: 'a', projectName: 'Project A' }; });
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
const snapshot = (projectId: string, document = emptyDiscovery(), revision: string | null = null, canEdit = true) => ({ projectId, document, revision, updatedAt: null, canEdit });
describe('project Discovery persistence UI', () => {
  it('saves explicitly and restores the server snapshot after remount', async () => {
    let saved = emptyDiscovery();
    const fetcher = vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.method === 'PUT') saved = JSON.parse(init.body as string).document;
      return Response.json(snapshot('a', saved, saved.sources.length ? 'a'.repeat(64) : null));
    });
    vi.stubGlobal('fetch', fetcher);
    const view = render(<DiscoveryClient />);
    await screen.findByRole('button', { name: 'Add evidence' });
    fireEvent.click(screen.getByRole('button', { name: 'Add evidence' }));
    expect(screen.getByText(/Unsaved draft/)).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Save draft' }));
    await screen.findByText('Draft saved in this project');
    expect(fetcher.mock.calls[1][0]).toBe('/api/projects/a/discovery');
    expect(JSON.parse(fetcher.mock.calls[1][1]!.body as string).expectedRevision).toBeNull();
    view.unmount(); render(<DiscoveryClient />);
    await screen.findByText('Evidence a');
    expect((screen.getByRole('button', { name: 'Save draft' }) as HTMLButtonElement).disabled).toBe(true);
  });
  it('retains unsaved drafts separately when changing projects', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => Response.json(snapshot(url.includes('/a/') ? 'a' : 'b'))));
    const view = render(<DiscoveryClient />);
    await screen.findByRole('button', { name: 'Add evidence' });
    fireEvent.click(screen.getByRole('button', { name: 'Add evidence' }));
    h.state = { projectId: 'b', projectName: 'Project B' }; view.rerender(<DiscoveryClient />);
    await screen.findByRole('button', { name: 'Add evidence' });
    expect(screen.queryByText('Evidence a')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Add evidence' }));
    h.state = { projectId: 'a', projectName: 'Project A' }; view.rerender(<DiscoveryClient />);
    await screen.findByText('Evidence a'); expect(screen.queryByText('Evidence b')).toBeNull();
  });
  it('ignores a late response from the previous project', async () => {
    let resolveA!: (response: Response) => void;
    vi.stubGlobal('fetch', vi.fn((url: string) => url.includes('/a/') ? new Promise<Response>((resolve) => { resolveA = resolve; }) : Promise.resolve(Response.json(snapshot('b')))));
    const view = render(<DiscoveryClient />);
    h.state = { projectId: 'b', projectName: 'Project B' }; view.rerender(<DiscoveryClient />);
    await screen.findByRole('button', { name: 'Add evidence' });
    resolveA(Response.json(snapshot('a', { ...emptyDiscovery(), sources: [{ id: 'private', name: 'Secret A', content: 'A', type: 'text', addedAt: '2026-09-07T10:00:00Z' }] })));
    await waitFor(() => expect(screen.queryByText('Secret A')).toBeNull());
    expect(screen.getByText(/Project B/)).toBeTruthy();
  });
  it('retains local evidence on a stale-save conflict and disables editing for a viewer', async () => {
    vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => init?.method === 'PUT' ? Response.json({ error: { message: 'A newer draft was saved elsewhere.' } }, { status: 409 }) : Response.json(snapshot('a'))));
    const view = render(<DiscoveryClient />);
    await screen.findByRole('button', { name: 'Add evidence' }); fireEvent.click(screen.getByRole('button', { name: 'Add evidence' }));
    fireEvent.click(screen.getByRole('button', { name: 'Save draft' }));
    await screen.findByRole('alert'); expect(screen.getByText('Evidence a')).toBeTruthy();
    view.unmount();
    vi.stubGlobal('fetch', vi.fn(async () => Response.json(snapshot('a', emptyDiscovery(), null, false))));
    render(<DiscoveryClient />); await screen.findByText(/Read-only project access/);
    expect((screen.getByRole('button', { name: 'Add evidence' }) as HTMLButtonElement).disabled).toBe(true);
  });
  it('never presents an editable empty draft after access denial', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Response.json({ error: { message: 'Forbidden' } }, { status: 403 })));
    render(<DiscoveryClient />); await screen.findByText(/Project access required/);
    expect(screen.queryByRole('button', { name: 'Add evidence' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Save draft' })).toBeNull();
  });
});
