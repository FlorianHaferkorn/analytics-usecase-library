import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const h = vi.hoisted(() => ({ fetch: vi.fn(), pin: vi.fn() }));

vi.mock('@/lib/store/project-store', () => ({
  useProjectStore: (selector: (state: { projectId: string; projectName: string; packageRevisionHash: string | null; setPackageRevisionHash: typeof h.pin }) => unknown) => selector({
    projectId: 'default',
    projectName: 'Aurora Group',
    packageRevisionHash: null,
    setPackageRevisionHash: h.pin,
  }),
}));

import { ProjectPackageClient } from '@/app/(studio)/package/project-package-client';

const HASH = 'a'.repeat(64);
const NEXT_HASH = 'b'.repeat(64);
const text = 'schema_version: 2.0.0\n';
const encoded = btoa(text);
const SNAPSHOT = {
  revision: {
    revision_hash: HASH,
    package_id: 'package_demo',
    project_ref: 'default',
    revision: 1,
    parent_revision_hash: null,
  },
  files: [{
    path: 'package.yaml',
    sha256: '0'.repeat(64),
    size: text.length,
    encoding: 'base64',
    contentBase64: encoded,
  }],
};

beforeEach(() => {
  h.fetch.mockReset();
  vi.stubGlobal('fetch', h.fetch);
});

describe('Project Package client', () => {
  it('offers verified history import when the project has no repository yet', async () => {
    h.fetch.mockResolvedValue(new Response(JSON.stringify({ error: { message: 'not found' } }), {
      status: 404,
      headers: { 'content-type': 'application/json' },
    }));
    render(<ProjectPackageClient />);

    expect(await screen.findByText('No package history')).toBeTruthy();
    expect(screen.getByText(/Import a repository ZIP/)).toBeTruthy();
  });

  it('commits a complete working copy and displays the resulting structural diff', async () => {
    h.fetch
      .mockResolvedValueOnce(new Response(JSON.stringify(SNAPSHOT), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        revision: {
          ...SNAPSHOT.revision,
          revision_hash: NEXT_HASH,
          revision: 2,
          parent_revision_hash: HASH,
        },
      }), { status: 201 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        from_revision_hash: HASH,
        to_revision_hash: NEXT_HASH,
        added_files: [],
        removed_files: [],
        changed_files: [{ path: 'package.yaml' }],
      }), { status: 200 }));

    render(<ProjectPackageClient />);
    const editor = await screen.findByLabelText('Edit package.yaml');
    fireEvent.change(editor, { target: { value: `${text}state: working\n` } });
    const save = await screen.findByRole('button', { name: 'Save 1 change' });
    expect((save as HTMLButtonElement).disabled).toBe(false);
    fireEvent.click(save);

    await waitFor(() => expect(screen.getByText('Saved revision 2.')).toBeTruthy());
    expect(screen.getByText('1 changed')).toBeTruthy();
    expect(h.fetch).toHaveBeenCalledTimes(3);
    const saveInit = h.fetch.mock.calls[1][1] as RequestInit;
    expect(JSON.parse(saveInit.body as string)).toMatchObject({ expectedHeadRevisionHash: HASH });
  });

  it.each([401, 403, 500])('does not claim empty or synchronized data after HTTP %i', async (status) => {
    h.fetch.mockResolvedValue(new Response(JSON.stringify({ error: { message: 'Access denied' } }), { status }));
    render(<ProjectPackageClient />);
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain(status === 401 ? 'Sign in required' : status === 403 ? 'Project access required' : 'Project Package unavailable');
    expect(screen.queryByText('Matches saved version')).toBeNull();
    expect(screen.queryByText('0.0 KiB total')).toBeNull();
    expect(screen.getByText('Not checked')).toBeTruthy();
    expect((screen.getByRole('button', { name: 'Export history' }) as HTMLButtonElement).disabled).toBe(true);
    if (status === 401) expect(screen.getByRole('link', { name: 'Sign in' }).getAttribute('href')).toContain('/login');
    else expect(screen.getByRole('button', { name: 'Try again' })).toBeTruthy();
  });

  it('recovers from a network load error without showing zero metrics', async () => {
    h.fetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce(new Response(JSON.stringify(SNAPSHOT), { status: 200 }));
    render(<ProjectPackageClient />);
    expect((await screen.findByRole('alert')).textContent).toContain('Check your connection');
    expect(screen.queryByText('Matches saved version')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
    expect(await screen.findByLabelText('Edit package.yaml')).toBeTruthy();
    expect(screen.getByText('Matches saved version')).toBeTruthy();
  });
});
