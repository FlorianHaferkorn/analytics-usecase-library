import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { usePinnedProject } from '@/components/project/use-pinned-project';

const state = vi.hoisted(() => ({ projectId: 'alpha', projectName: 'Alpha', packageRevisionHash: null as string | null, setPackageRevisionHash: vi.fn() }));
vi.mock('@/lib/store/project-store', () => ({ useProjectStore: Object.assign((selector: (value: typeof state) => unknown) => selector(state), { getState: () => state }) }));
const oldHash = 'a'.repeat(64), newHash = 'b'.repeat(64);
beforeEach(() => { state.projectId = 'alpha'; state.packageRevisionHash = oldHash; state.setPackageRevisionHash.mockClear(); });
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe('Pinned Package response ordering', () => {
  it.each([oldHash, null])('does not repin a stale response after selection changes from %s', async initial => {
    state.packageRevisionHash = initial;
    let resolve!: (response: Response) => void;
    vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(done => { resolve = done; })));
    renderHook(() => usePinnedProject());
    // Store mutation precedes React's passive-effect cleanup; the request is not yet aborted.
    state.packageRevisionHash = newHash;
    await act(async () => resolve({ ok: true, json: async () => ({ projectId: 'alpha', revision: { revision_hash: oldHash } }) } as Response));
    expect(state.setPackageRevisionHash).not.toHaveBeenCalled();
  });
  it('pins a current response', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ projectId: 'alpha', revision: { revision_hash: oldHash } }) })));
    renderHook(() => usePinnedProject());
    await waitFor(() => expect(state.setPackageRevisionHash).toHaveBeenCalledWith(oldHash));
  });
});
