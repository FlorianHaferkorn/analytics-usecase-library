import { beforeEach, describe, expect, it, vi } from 'vitest';

const { runGenerateMock, auditMock } = vi.hoisted(() => ({
  runGenerateMock: vi.fn(),
  auditMock: vi.fn(),
}));

vi.mock('@/lib/bridge/superversion-bridge', () => ({
  runGenerate: runGenerateMock,
}));

vi.mock('@/lib/db/audit-helpers', () => ({
  auditWithActor: auditMock,
}));

import { processGovernedExportRequest } from '@/lib/delivery/governed-export-handler';

function request(useCaseIds: unknown): Request {
  return new Request('http://studio.test/api/export/fabric', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ useCaseIds }),
  });
}

function green(target: string) {
  return {
    available: true,
    ok: true,
    bracket: 'COM-001_Sales_Performance',
    target,
    targetLabel: target.toUpperCase(),
    targetStatus: 'live',
    targetsAvailable: ['tmdl', 'pbir'],
    artifacts: [{ path: `COM-001/${target}.txt`, bytes: 3, content: 'ok\n' }],
    gate: { ok: true, stages: [{ name: target, status: 'PASS', detail: 'green' }] },
  };
}

beforeEach(() => {
  runGenerateMock.mockReset();
  auditMock.mockReset();
  auditMock.mockResolvedValue(undefined);
});

describe('processGovernedExportRequest', () => {
  it('never passes a project-scoped request into the global catalog generator', async () => {
    const req = new Request('http://x/api/projects/project_demo/export/fabric', { method: 'POST', body: JSON.stringify({ useCaseIds: ['COM-001'] }) });
    expect((await processGovernedExportRequest(req, ['pbir'], 'fabric')).status).toBe(409);
    expect(runGenerateMock).not.toHaveBeenCalled();
  });
  it('packages only artifacts returned by the governed bridge and adds a gate manifest', async () => {
    runGenerateMock.mockImplementation((_id: string, target: string, includeContent: boolean) => {
      expect(includeContent).toBe(true);
      return Promise.resolve(green(target));
    });

    const response = await processGovernedExportRequest(request(['COM-001']), ['tmdl', 'pbir'], 'fabric');
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.results[0].outputs.tmdl[0].content).toBe('ok\n');
    expect(body.results[0].outputs.pbir[0].content).toBe('ok\n');
    expect(JSON.parse(body.results[0].outputs.manifest[0].content).targets).toHaveLength(2);
    expect(auditMock).toHaveBeenCalledOnce();
  });

  it('blocks the use case package when any shared gate is red', async () => {
    runGenerateMock
      .mockResolvedValueOnce(green('tmdl'))
      .mockResolvedValueOnce({ ...green('pbir'), ok: false, error: 'PBIR gate failed' });

    const response = await processGovernedExportRequest(request(['COM-001']), ['tmdl', 'pbir'], 'fabric');
    const body = await response.json();

    expect(body.results[0]).toEqual({ useCaseId: 'COM-001', error: 'PBIR gate failed' });
  });

  it('rejects invalid IDs before starting generator processes', async () => {
    const response = await processGovernedExportRequest(request(['../../escape']), ['pbir'], 'fabric');
    const body = await response.json();

    expect(response.status).toBe(422);
    expect(body.error.details[0]).toContain('Invalid use case IDs');
    expect(runGenerateMock).not.toHaveBeenCalled();
  });

  it('rejects duplicate use cases before package assembly', async () => {
    const response = await processGovernedExportRequest(request(['COM-001', 'COM-001']), ['pbir'], 'fabric');
    const body = await response.json();

    expect(response.status).toBe(422);
    expect(body.error.details[0]).toContain('Duplicate');
    expect(runGenerateMock).not.toHaveBeenCalled();
  });

  it('fails honestly when the bridge omits requested artifact content', async () => {
    runGenerateMock.mockResolvedValue({
      ...green('osi'),
      artifacts: [{ path: 'model.json', bytes: 12 }],
    });

    const response = await processGovernedExportRequest(request(['COM-001']), ['osi'], 'osi');
    const body = await response.json();

    expect(body.results[0].error).toContain('artifact content missing');
  });
});
