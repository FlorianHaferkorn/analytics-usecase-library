import { beforeEach, describe, expect, it, vi } from 'vitest';
import { emptyDiscovery } from '@/lib/discovery/document';
const h = vi.hoisted(() => ({ role: vi.fn(), project: vi.fn(), read: vi.fn(), write: vi.fn() }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: h.role }));
vi.mock('@/lib/db/project-repo', () => ({ getProject: h.project }));
vi.mock('@/lib/db/discovery-repo', () => ({ readDiscovery: h.read, writeDiscovery: h.write }));
import { GET, PUT } from '@/app/api/projects/[projectId]/discovery/route';
const context = { params: Promise.resolve({ projectId: 'customer-a' }) };
const request = (body: unknown) => new Request('http://test/api/projects/customer-a/discovery', { method: 'PUT', body: JSON.stringify(body) });
beforeEach(() => { vi.clearAllMocks(); h.role.mockResolvedValue([{ email: 'editor@example.com' }, null]); h.project.mockReturnValue({ id: 'customer-a' }); h.read.mockReturnValue({ document: emptyDiscovery(), revision: null }); h.write.mockReturnValue({ document: emptyDiscovery(), revision: 'a'.repeat(64) }); });
describe('project-scoped Discovery routes', () => {
  it.each([401, 403])('denies %s before reading or writing project data', async (status) => {
    h.role.mockImplementation(async () => [null, new Response('', { status })]);
    expect((await GET(new Request('http://test'), context)).status).toBe(status);
    expect((await PUT(request({}), context)).status).toBe(status);
    expect(h.read).not.toHaveBeenCalled(); expect(h.write).not.toHaveBeenCalled();
  });
  it('uses explicit viewer/editor roles and the route project, never a payload fallback', async () => {
    expect((await GET(new Request('http://test'), context)).headers.get('Cache-Control')).toBe('no-store');
    expect(h.role).toHaveBeenCalledWith('viewer', 'customer-a');
    const response = await PUT(request({ document: emptyDiscovery(), expectedRevision: null, projectId: 'other' }), context);
    expect(response.status).toBe(200); expect(h.role).toHaveBeenCalledWith('editor', 'customer-a');
    expect(h.write).toHaveBeenCalledWith('customer-a', emptyDiscovery(), null, 'editor@example.com');
  });
  it('requires a revision and rejects invalid candidate schema', async () => {
    expect((await PUT(request({ document: emptyDiscovery() }), context)).status).toBe(422);
    expect((await PUT(request({ document: { ...emptyDiscovery(), candidates: [{ status: 'approved' }] }, expectedRevision: null }), context)).status).toBe(422);
    expect(h.write).not.toHaveBeenCalled();
  });
  it('returns a conflict instead of silently overwriting a newer draft', async () => {
    h.write.mockReturnValue(null);
    expect((await PUT(request({ document: emptyDiscovery(), expectedRevision: null }), context)).status).toBe(409);
  });
});
