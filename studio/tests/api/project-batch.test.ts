import { createHash } from 'node:crypto';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const fake = vi.hoisted(() => ({ role: vi.fn(), batch: vi.fn() }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: fake.role }));
vi.mock('@/lib/bridge/project-batch', () => ({ projectBatch: fake.batch }));
import { GET, POST } from '@/app/api/projects/[projectId]/ingestion/route';

const revision = 'a'.repeat(64);
const nextRevision = 'b'.repeat(64);
const previewHash = 'c'.repeat(64);
const context = { params: Promise.resolve({ projectId: 'alpha' }) };
const url = 'http://localhost:3000/api/projects/alpha/ingestion';
const post = (body: unknown, headers: Record<string, string> = {}) => new Request(url, {
  method: 'POST', headers: { origin: 'http://localhost:3000', 'content-type': 'application/json', ...headers }, body: JSON.stringify(body),
});
const preview = { revisionHash: revision, mode: 'preview', contract: { id: 'orders' } };
const save = { ...preview, mode: 'save', previewHash, confirmed: true, rationale: 'Use the reviewed environment and loading contract.' };
const test = { revisionHash: revision, mode: 'test', confirmed: true, batches: [{ batch_id: 'one', rows: [{ id: 1 }] }] };
const generate = { revisionHash: revision, mode: 'export', confirmed: true };
const scoped = { project_ref: 'alpha', revision_hash: revision };
const digest = (value: string) => createHash('sha256').update(value, 'utf8').digest('hex');
function output() {
  const files = [{ path: 'contract.json', content: '{"id":"orders"}\n' }, { path: 'runtime/README.md', content: 'Local rows only. No tenant actions.\n' }];
  const manifest = { ...scoped, files: files.map(file => ({ path: file.path, sha256: digest(file.content) })) };
  return { output_type: 'batch_ingestion_bundle', manifest, files: [...files, { path: 'output-manifest.json', content: JSON.stringify(manifest) }], limitations: ['No tenant proof'] };
}

beforeEach(() => {
  vi.clearAllMocks();
  fake.role.mockResolvedValue([{ email: 'session-user@example.test' }, null]);
  fake.batch.mockImplementation(async (_project, _revision, mode) => ({ available: true, ok: true, value:
    mode === 'save' ? { project_ref: 'alpha', revision_hash: nextRevision, parent_revision_hash: revision, state: 'working', release_required: true, tenant_actions_performed: false }
      : mode === 'test' ? { ...scoped, evidence_kind: 'local_check', tenant_actions_performed: false, batches: [] }
        : mode === 'export' ? output() : { ...scoped, preview_hash: previewHash, can_save: true },
  }));
});

describe('Project batch ingestion API boundary', () => {
  it('authorizes reads and writes before accessing the bridge or parsing input', async () => {
    fake.role.mockResolvedValue([null, new Response('denied', { status: 403 })]);
    expect((await GET(new Request(`${url}?revision=${revision}`), context)).status).toBe(403);
    expect((await POST(new Request(url, { method: 'POST', body: '{' }), context)).status).toBe(403);
    expect(fake.batch).not.toHaveBeenCalled();
  });

  it('reads only the pinned version under project viewer authorization', async () => {
    expect((await GET(new Request(url), context)).status).toBe(422);
    expect((await GET(new Request(`${url}?revision=../bad`), context)).status).toBe(422);
    const response = await GET(new Request(`${url}?revision=${revision}`), context);
    expect(response.status).toBe(200);
    expect(fake.role).toHaveBeenCalledWith('viewer', 'alpha');
    expect(fake.batch).toHaveBeenCalledExactlyOnceWith('alpha', revision, 'inspect');
    expect(response.headers.get('cache-control')).toBe('private, no-store');
  });

  it.each([{ project_ref: 'other', revision_hash: revision }, { ...scoped, revision_hash: nextRevision }])('rejects foreign read provenance %o', async value => {
    fake.batch.mockResolvedValue({ ok: true, value });
    expect((await GET(new Request(`${url}?revision=${revision}`), context)).status).toBe(409);
  });

  it.each([['origin', 'http://evil.test'], ['origin', ''], ['sec-fetch-site', 'cross-site'], ['content-type', 'text/plain']])('requires same-origin JSON: %s=%s', async (key, value) => {
    expect((await POST(post(preview, { [key]: value }), context)).status).toBe(403);
    expect(fake.batch).not.toHaveBeenCalled();
  });

  it('rejects malformed and oversized bodies', async () => {
    expect((await POST(new Request(url, { method: 'POST', headers: { origin: 'http://localhost:3000', 'content-type': 'application/json' }, body: '{' }), context)).status).toBe(400);
    expect((await POST(post({ ...preview, padding: 'x'.repeat(256001) }), context)).status).toBe(413);
    expect(fake.batch).not.toHaveBeenCalled();
  });

  it.each([null, [], 1, { ...preview, mode: 'apply' }, { ...preview, mode: 'inspect' }, { ...preview, revisionHash: 'latest' },
    { ...preview, actor: 'admin' }, { ...preview, repository: 'C:/customer' }, { ...preview, credentials: {} }, { ...preview, state: {} },
    { ...preview, project_ref: 'customer' }, { ...preview, contract: [] }, { ...preview, contract: null }, { ...generate, command: 'fab rm' }])('rejects open body or unsupported input %o', async body => {
    expect((await POST(post(body), context)).status).toBe(422);
    expect(fake.batch).not.toHaveBeenCalled();
  });

  it('previews without trusting client identity or invoking save', async () => {
    const response = await POST(post(preview), context);
    expect(response.status).toBe(200);
    expect(fake.batch).toHaveBeenCalledExactlyOnceWith('alpha', revision, 'preview', { contract: preview.contract });
    expect(response.headers.get('cache-control')).toBe('private, no-store');
  });

  it('requires editor authorization for saving and uses that server identity', async () => {
    fake.role.mockResolvedValueOnce([{ email: 'viewer@example.test' }, null]).mockResolvedValueOnce([{ email: 'editor@example.test' }, null]);
    const response = await POST(post(save), context);
    expect(response.status).toBe(200);
    expect(fake.role).toHaveBeenNthCalledWith(1, 'viewer', 'alpha');
    expect(fake.role).toHaveBeenNthCalledWith(2, 'editor', 'alpha');
    expect(fake.batch).toHaveBeenCalledExactlyOnceWith('alpha', revision, 'save', {
      contract: preview.contract, preview_hash: previewHash, actor: 'editor@example.test', rationale: save.rationale, confirmed: true,
    });
  });

  it('never saves when editor authorization is denied', async () => {
    fake.role.mockResolvedValueOnce([{ email: 'viewer@example.test' }, null]).mockResolvedValueOnce([null, new Response('denied', { status: 403 })]);
    expect((await POST(post(save), context)).status).toBe(403);
    expect(fake.batch).not.toHaveBeenCalled();
  });

  it.each([{ confirmed: false }, { confirmed: 'true' }, { previewHash: 'old' }, { rationale: 'short' }, { rationale: ' '.repeat(30) }, { rationale: 'x'.repeat(2001) }])('requires reviewed preview and meaningful confirmation %o', async extra => {
    expect((await POST(post({ ...save, ...extra }), context)).status).toBe(422);
    expect(fake.batch).not.toHaveBeenCalled();
  });

  it.each([{ confirmed: false }, { batches: [] }, { batches: Array(4).fill({ batch_id: 'one', rows: [] }) },
    { batches: [{ batch_id: 'one', rows: Array(1001).fill({ id: 1 }) }] }, { batches: [{ batch_id: 'one', rows: [], state: {} }] },
    { batches: [{ batch_id: 1, rows: [] }] }, { batches: [{ batch_id: 'one', rows: {} }] }])('bounds local tests and disallows imported state %o', async extra => {
    expect((await POST(post({ ...test, ...extra }), context)).status).toBe(422);
    expect(fake.batch).not.toHaveBeenCalled();
  });

  it('runs only explicit bounded test rows and preserves evidence scope', async () => {
    expect((await POST(post(test), context)).status).toBe(200);
    expect(fake.batch).toHaveBeenCalledExactlyOnceWith('alpha', revision, 'test', { batches: test.batches });
  });

  it.each([{ evidence_kind: 'tenant_verified', tenant_actions_performed: false }, { evidence_kind: 'local_check', tenant_actions_performed: true }, { evidence_kind: 'simulation', tenant_actions_performed: false }])('rejects inappropriate test claims %o', async extra => {
    fake.batch.mockResolvedValue({ ok: true, value: { ...scoped, ...extra } });
    expect((await POST(post(test), context)).status).toBe(409);
  });

  it.each([{ parent_revision_hash: nextRevision }, { state: 'released' }, { release_required: false }, { tenant_actions_performed: true }, { revision_hash: revision }])('rejects invalid save provenance %o', async extra => {
    fake.batch.mockResolvedValue({ ok: true, value: { project_ref: 'alpha', revision_hash: nextRevision, parent_revision_hash: revision, state: 'working', release_required: true, tenant_actions_performed: false, ...extra } });
    expect((await POST(post(save), context)).status).toBe(409);
  });

  it.each(['preview', 'test'])('rejects another version for %s', async mode => {
    fake.batch.mockResolvedValue({ ok: true, value: { ...scoped, revision_hash: nextRevision, evidence_kind: 'local_check', tenant_actions_performed: false } });
    expect((await POST(post(mode === 'preview' ? preview : test), context)).status).toBe(409);
  });

  it('requires explicit export confirmation', async () => {
    expect((await POST(post({ ...generate, confirmed: false }), context)).status).toBe(422);
    expect(fake.batch).not.toHaveBeenCalled();
  });

  it('exports only matching scoped content with correct file hashes', async () => {
    const response = await POST(post(generate), context);
    expect(response.status).toBe(200);
    expect(fake.batch).toHaveBeenCalledExactlyOnceWith('alpha', revision, 'export', {});
    expect(response.headers.get('cache-control')).toBe('private, no-store');
    expect((await response.json()).manifest.revision_hash).toBe(revision);
  });

  it.each(['../escape', '/absolute', 'C:/secret', 'nested\\escape', 'nested//empty', './same'])('rejects unsafe export paths %s', async path => {
    const value = output(); value.files[0].path = path;
    fake.batch.mockResolvedValue({ ok: true, value });
    expect((await POST(post(generate), context)).status).toBe(409);
  });

  it.each(['scope', 'hash', 'duplicate_path', 'unlisted_file', 'missing_file', 'duplicate_manifest'])('rejects inconsistent export inventory %s', async kind => {
    const value = output();
    if (kind === 'scope') value.manifest.project_ref = 'other';
    if (kind === 'hash') value.files[0].content += 'tampered';
    if (kind === 'duplicate_path') value.files.push({ path: 'CONTRACT.JSON', content: '{}' });
    if (kind === 'unlisted_file') value.files.push({ path: 'unlisted.txt', content: 'unverified' });
    if (kind === 'missing_file') value.files.splice(0, 1);
    if (kind === 'duplicate_manifest') value.manifest.files.push({ ...value.manifest.files[0] });
    fake.batch.mockResolvedValue({ ok: true, value });
    expect((await POST(post(generate), context)).status).toBe(409);
  });

  it('accepts equivalent manifest JSON independent of object property ordering', async () => {
    const value = output();
    value.files.at(-1)!.content = JSON.stringify({ files: value.manifest.files.map(item => ({ sha256: item.sha256, path: item.path })), revision_hash: revision, project_ref: 'alpha' });
    fake.batch.mockResolvedValue({ ok: true, value });
    expect((await POST(post(generate), context)).status).toBe(200);
  });

  it.each(['null_file', 'empty_inventory', 'missing_manifest', 'mismatched_manifest'])('fails closed on malformed export shape %s', async kind => {
    const value = output();
    if (kind === 'null_file') value.files = [null as unknown as typeof value.files[number]];
    if (kind === 'empty_inventory') { value.files = []; value.manifest.files = []; }
    if (kind === 'missing_manifest') value.files.pop();
    if (kind === 'mismatched_manifest') value.files.at(-1)!.content = JSON.stringify({ ...value.manifest, project_ref: 'foreign' });
    fake.batch.mockResolvedValue({ ok: true, value });
    expect((await POST(post(generate), context)).status).toBe(409);
  });

  it('does not convert backend failures or stale release into success', async () => {
    fake.batch.mockResolvedValue({ ok: false, status: 409, error: 'The pinned release is stale.' });
    const response = await POST(post(generate), context);
    expect(response.status).toBe(409);
    expect((await response.json()).error).toBe('The pinned release is stale.');
    fake.batch.mockResolvedValue({ ok: false, available: false, error: 'Local engine unavailable.' });
    expect((await GET(new Request(`${url}?revision=${revision}`), context)).status).toBe(503);
  });
});
