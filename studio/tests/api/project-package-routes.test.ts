import { beforeEach, describe, expect, it, vi } from 'vitest';

const h = vi.hoisted(() => ({
  requireRole: vi.fn(),
  getProject: vi.fn(),
  load: vi.fn(),
  commit: vi.fn(),
  diff: vi.fn(),
  exportHistory: vi.fn(),
  importHistory: vi.fn(),
  audit: vi.fn(),
}));

vi.mock('@/lib/auth/require-role', () => ({ requireRole: h.requireRole }));
vi.mock('@/lib/db/project-repo', () => ({ getProject: h.getProject }));
vi.mock('@/lib/db/audit-repo', () => ({ logAuditEvent: h.audit }));
vi.mock('@/lib/bridge/project-package-repository', () => ({
  loadProjectPackage: h.load,
  commitProjectPackageDraft: h.commit,
  diffPackageRevisions: h.diff,
  exportProjectPackageHistory: h.exportHistory,
  importProjectPackageHistory: h.importHistory,
}));

const PROJECT_ID = 'project_demo';
const HASH = 'a'.repeat(64);
const REVISION = {
  revision_hash: HASH,
  package_id: 'package_demo',
  project_ref: PROJECT_ID,
  revision: 1,
  parent_revision_hash: null,
};
const CONTEXT = { params: Promise.resolve({ projectId: PROJECT_ID }) };
const FILE = {
  path: 'package.yaml',
  sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
  size: 0,
  encoding: 'base64' as const,
  contentBase64: '',
};

beforeEach(() => {
  vi.clearAllMocks();
  h.requireRole.mockResolvedValue([{ email: 'editor@example.com', name: 'Editor' }, null]);
  h.getProject.mockReturnValue({ id: PROJECT_ID });
});

describe('Project Package API routes', () => {
  it('loads a complete package snapshot for a viewer', async () => {
    h.load.mockResolvedValue({
      available: true,
      ok: true,
      value: { revision: REVISION, files: [FILE] },
    });
    const { GET } = await import('@/app/api/projects/[projectId]/package/route');
    const response = await GET(new Request(`http://x/api/projects/${PROJECT_ID}/package`), CONTEXT);

    expect(response.status).toBe(200);
    expect(h.requireRole).toHaveBeenCalledWith('viewer', PROJECT_ID);
    expect(await response.json()).toEqual({ revision: REVISION, files: [FILE] });
  });

  it('maps a stale editor save to HTTP 409 without writing an audit event', async () => {
    h.commit.mockResolvedValue({
      available: true,
      ok: false,
      status: 409,
      code: 'stale_head',
      error: 'expected HEAD does not match current HEAD',
    });
    const { POST } = await import('@/app/api/projects/[projectId]/package/route');
    const response = await POST(new Request(`http://x/api/projects/${PROJECT_ID}/package`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ expectedHeadRevisionHash: HASH, files: [FILE] }),
    }), CONTEXT);

    expect(response.status).toBe(409);
    expect(h.requireRole).toHaveBeenCalledWith('editor', PROJECT_ID);
    expect(h.audit).not.toHaveBeenCalled();
  });

  it('audits only immutable revision metadata after a successful save', async () => {
    const nextRevision = { ...REVISION, revision_hash: 'b'.repeat(64), revision: 2, parent_revision_hash: HASH };
    h.commit.mockResolvedValue({ available: true, ok: true, value: nextRevision });
    const { POST } = await import('@/app/api/projects/[projectId]/package/route');
    const response = await POST(new Request(`http://x/api/projects/${PROJECT_ID}/package`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ expectedHeadRevisionHash: HASH, files: [FILE] }),
    }), CONTEXT);

    expect(response.status).toBe(201);
    expect(h.audit).toHaveBeenCalledOnce();
    expect(JSON.stringify(h.audit.mock.calls[0])).not.toContain('contentBase64');
  });

  it('requires an admin and rejects an oversized history import before the bridge', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/package/import/route');
    const response = await POST(new Request(`http://x/api/projects/${PROJECT_ID}/package/import`, {
      method: 'POST',
      headers: { 'content-length': String(101 * 1024 * 1024) },
      body: new Uint8Array([1]),
    }), CONTEXT);

    expect(response.status).toBe(413);
    expect(h.requireRole).toHaveBeenCalledWith('admin', PROJECT_ID);
    expect(h.importHistory).not.toHaveBeenCalled();
  });

  it('exports verified history as a ZIP and records its HEAD hash', async () => {
    h.exportHistory.mockResolvedValue({
      available: true,
      ok: true,
      value: { archive: new Uint8Array([80, 75, 3, 4]), head: REVISION },
    });
    const { GET } = await import('@/app/api/projects/[projectId]/package/export/route');
    const response = await GET(new Request(`http://x/api/projects/${PROJECT_ID}/package/export`), CONTEXT);

    expect(response.status).toBe(200);
    expect(response.headers.get('content-type')).toBe('application/zip');
    expect(response.headers.get('x-package-revision')).toBe(HASH);
    expect(h.audit).toHaveBeenCalledOnce();
  });
});
