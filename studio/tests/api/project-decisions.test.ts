import { beforeEach, describe, expect, it, vi } from 'vitest';
const mocks = vi.hoisted(() => ({ role: vi.fn(), engine: vi.fn() }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: mocks.role }));
vi.mock('@/lib/bridge/project-decisions', () => ({ projectDecisions: mocks.engine }));
const hash = 'a'.repeat(64), next = 'b'.repeat(64), preview = 'c'.repeat(64);
const context = { params: Promise.resolve({ projectId: 'alpha' }) };
const post = (body: unknown) => new Request('http://x/decisions', { method: 'POST', body: JSON.stringify(body) });
const valid = { revisionHash: hash, previewHash: preview, rationale: 'Reviewed the explicit approved mapping.', confirmed: true };
beforeEach(() => {
  vi.clearAllMocks();
  mocks.role.mockResolvedValue([{ email: 'reviewer@example.test' }, null]);
  mocks.engine.mockResolvedValue({ ok: true, value: { project_ref: 'alpha', revision_hash: next, parent_revision_hash: hash, state: 'working', release_required: true } });
});
describe('Reviewed decision derivation API', () => {
  it('authorizes the project before reading or mutating it', async () => {
    const { GET, POST } = await import('@/app/api/projects/[projectId]/architecture/decisions/route');
    mocks.role.mockResolvedValue([null, new Response('denied', { status: 403 })]);
    expect((await GET(new Request(`http://x?revision=${hash}`), context)).status).toBe(403);
    expect((await POST(post(valid), context)).status).toBe(403);
    expect(mocks.engine).not.toHaveBeenCalled();
  });
  it('requires a pinned revision and prevents caching', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/decisions/route');
    expect((await GET(new Request('http://x'), context)).status).toBe(422);
    mocks.engine.mockResolvedValue({ ok: true, value: { project_ref: 'alpha', revision_hash: hash } });
    const response = await GET(new Request(`http://x?revision=${hash}`), context);
    expect(response.status).toBe(200);
    expect(response.headers.get('cache-control')).toBe('private, no-store');
    expect(mocks.role).toHaveBeenCalledWith('viewer', 'alpha');
    expect(mocks.engine).toHaveBeenCalledWith('alpha', hash);
  });
  it('rejects a foreign preview', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/decisions/route');
    mocks.engine.mockResolvedValue({ ok: true, value: { project_ref: 'beta', revision_hash: hash } });
    expect((await GET(new Request(`http://x?revision=${hash}`), context)).status).toBe(409);
  });
  it('accepts only confirmation and hashes, never browser values or authority', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/architecture/decisions/route');
    for (const patch of [{ actor: 'admin' }, { changes: [] }, { rule: {} }, { confirmed: false }, { revisionHash: 'HEAD' }, { previewHash: '' }, { rationale: 'yes' }]) {
      expect((await POST(post({ ...valid, ...patch }), context)).status).toBe(422);
    }
    expect(mocks.engine).not.toHaveBeenCalled();
  });
  it('binds a write to the session identity and reviewed preview', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/architecture/decisions/route');
    const response = await POST(post(valid), context);
    expect(response.status).toBe(200);
    expect(mocks.role).toHaveBeenCalledWith('editor', 'alpha');
    expect(mocks.engine).toHaveBeenCalledWith('alpha', hash, { previewHash: preview, rationale: valid.rationale, actor: 'reviewer@example.test' });
  });
  it('returns stale/conflicting results without pretending an update succeeded', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/architecture/decisions/route');
    mocks.engine.mockResolvedValue({ ok: false, status: 409, error: 'HEAD changed' });
    expect((await POST(post(valid), context)).status).toBe(409);
  });
  it('checks the returned parent and project before announcing success', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/architecture/decisions/route');
    mocks.engine.mockResolvedValue({ ok: true, value: { project_ref: 'alpha', revision_hash: next, parent_revision_hash: next } });
    expect((await POST(post(valid), context)).status).toBe(409);
  });
  it('rejects oversized and malformed input', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/architecture/decisions/route');
    expect((await POST(post({ ...valid, rationale: 'x'.repeat(13000) }), context)).status).toBe(413);
    expect((await POST(new Request('http://x', { method: 'POST', body: '{' }), context)).status).toBe(400);
    expect(mocks.engine).not.toHaveBeenCalled();
  });
});
