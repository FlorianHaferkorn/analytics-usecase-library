import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { GovernedPreview } from '@/components/delivery/governed-preview';

const precoreBody = { available: true, ok: true, bracket: 'COM-001', engines: [] };
const generateBody = {
  available: true,
  ok: true,
  bracket: 'COM-001',
  target: 'tmdl',
  targetsAvailable: ['tmdl', 'pbir'],
  artifacts: [{ path: 'x.tmdl', bytes: 10 }],
  gate: { ok: true, stages: [{ name: 'tmdl', status: 'PASS' as const, detail: '1 file(s)' }] },
};
const flowBody = {
  bracketId: 'COM-001',
  canHandoff: false,
  blockedReason: 'Nicht freigegeben (Freigabe-Schleuse offen)',
  steps: [
    { key: 'authoring', label: 'Authoring', status: 'done', detail: 'Bracket COM-001' },
    { key: 'approval', label: 'Freigabe-Schleuse', status: 'pending', detail: 'Entwurf' },
    { key: 'generate', label: 'Generate', status: 'pending', detail: 'noch nicht ausgeführt' },
    { key: 'validate', label: 'Validate (Gate)', status: 'pending', detail: 'Gate noch nicht gelaufen' },
    { key: 'deliverable', label: 'Deliverable', status: 'blocked', detail: 'Nicht freigegeben (Freigabe-Schleuse offen)' },
  ],
};

describe('GovernedPreview', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      const body = url.includes('/api/precore')
        ? precoreBody
        : url.includes('/api/generate')
          ? generateBody
          : flowBody;
      return Promise.resolve({ json: () => Promise.resolve(body) } as Response);
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('fetches precore, generate, and delivery-flow for the bracket and renders all three panels', async () => {
    render(<GovernedPreview bracketId="COM-001" target="tmdl" />);

    expect(screen.getByTestId('governed-preview-loading')).toBeDefined();

    await waitFor(() => expect(screen.getByTestId('governed-preview')).toBeDefined());

    expect(screen.getByTestId('precore-panel')).toBeDefined();
    expect(screen.getByTestId('gate-report-panel')).toBeDefined();
    expect(screen.getByTestId('delivery-flow-panel')).toBeDefined();

    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    const calledUrls = fetchMock.mock.calls.map((c: unknown[]) => c[0] as string);
    expect(calledUrls.some((u) => u.startsWith('/api/precore?bracketId=COM-001'))).toBe(true);
    expect(calledUrls.some((u) => u.startsWith('/api/generate?bracketId=COM-001&target=tmdl'))).toBe(true);
    expect(calledUrls.some((u) => u.startsWith('/api/delivery-flow?bracketId=COM-001&target=tmdl'))).toBe(true);
  });

  it('shows an honest unavailable state when the bridge request itself fails', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('network down'))));

    render(<GovernedPreview bracketId="COM-001" target="tmdl" />);
    await waitFor(() => expect(screen.getByTestId('governed-preview')).toBeDefined());

    expect(screen.getByTestId('precore-unavailable')).toBeDefined();
    expect(screen.getByTestId('generate-unavailable')).toBeDefined();
  });
});
