import { beforeEach, expect, it, vi } from 'vitest';
const h = vi.hoisted(() => ({ role: vi.fn(), project: vi.fn(), release: vi.fn() }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: h.role }));
vi.mock('@/lib/db/project-repo', () => ({ getProject: h.project }));
vi.mock('@/lib/bridge/project-package-repository', () => ({ exportApprovedProjectInput: h.release }));
import { GET, POST } from '@/app/api/projects/[projectId]/package/release/route';
const hash = 'a'.repeat(64);
const context = { params: Promise.resolve({ projectId: 'project_demo' }) };
beforeEach(() => {
  vi.clearAllMocks();
  h.role.mockResolvedValue([{ email: 'admin@example.test' }, null]);
  h.project.mockReturnValue({ id: 'project_demo' });
  h.release.mockResolvedValue({ available: true, ok: true, value: { release: { record_sha256: 'b'.repeat(64) }, files: [] } });
});
it('requires explicit admin confirmation and records the authenticated actor, never a body actor', async () => {
  const response = await POST(new Request('http://x/api/projects/project_demo/package/release', { method: 'POST', body: JSON.stringify({ revisionHash: hash, rationale: 'Reviewed the immutable approved inputs.', confirmInputBundleRelease: true, actor: 'forged' }) }), context);
  expect(response.status).toBe(200);
  expect(h.role).toHaveBeenCalledWith('admin', 'project_demo');
  expect(h.release).toHaveBeenCalledWith('project_demo', hash, { actor: 'admin@example.test', rationale: 'Reviewed the immutable approved inputs.' });
  expect(response.headers.get('x-package-revision')).toBe(hash);
});
it('does not invoke release storage when access is denied', async () => {
  h.role.mockResolvedValue([null, new Response('Forbidden', { status: 403 })]);
  expect((await POST(new Request('http://x/', { method: 'POST', body: '{}' }), context)).status).toBe(403);
  expect(h.release).not.toHaveBeenCalled();
});
it('does not infer approval from a valid hash alone', async () => {
  expect((await POST(new Request('http://x/', { method: 'POST', body: JSON.stringify({ revisionHash: hash, rationale: 'This does not confirm release approval.' }) }), context)).status).toBe(422);
  expect(h.release).not.toHaveBeenCalled();
});
it('reads only the pinned existing release as viewer and preserves stale errors', async () => {
  h.release.mockResolvedValue({ available: true, ok: false, code: 'stale_head', error: 'Selected revision is stale' });
  expect((await GET(new Request(`http://x/?revision=${hash}`), context)).status).toBe(409);
  expect(h.role).toHaveBeenCalledWith('viewer', 'project_demo');
  expect(h.release).toHaveBeenCalledWith('project_demo', hash, undefined);
});
