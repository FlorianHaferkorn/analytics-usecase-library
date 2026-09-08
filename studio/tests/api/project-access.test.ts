import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({ auth: vi.fn(), role: vi.fn(), list: vi.fn(), user: vi.fn(), access: vi.fn(), get: vi.fn() }));
vi.mock('@/lib/auth/session', () => ({ requireAuth: mocks.auth }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: mocks.role }));
vi.mock('@/lib/db/project-repo', () => ({ listProjects: mocks.list, getProject: mocks.get, updateProject: vi.fn(), createProject: vi.fn() }));
vi.mock('@/lib/db/user-repo', () => ({ findOrCreateUser: mocks.user }));
vi.mock('@/lib/db/rbac-repo', () => ({ checkAccess: mocks.access, addProjectMember: vi.fn() }));
vi.mock('@/lib/db/audit-repo', () => ({ logAuditEvent: vi.fn() }));

beforeEach(() => { vi.clearAllMocks(); });

describe('Project metadata access', () => {
  it('does not enumerate projects before authentication', async () => {
    mocks.auth.mockResolvedValue([null, new Response('Sign in', { status: 401 })]);
    const { GET } = await import('@/app/api/project/list/route');
    expect((await GET()).status).toBe(401);
    expect(mocks.list).not.toHaveBeenCalled();
  });

  it('lists only projects the authenticated user can view', async () => {
    mocks.auth.mockResolvedValue([{ email: 'reader@example.org', name: 'Reader' }, null]);
    mocks.user.mockReturnValue({ id: 'reader' });
    mocks.list.mockReturnValue([{ id: 'alpha', name: 'Alpha' }, { id: 'beta', name: 'Private Beta' }]);
    mocks.access.mockImplementation((id: string) => id === 'alpha');
    const { GET } = await import('@/app/api/project/list/route');
    const response = await GET();
    expect(response.status).toBe(200);
    const body = await response.text();
    expect(body).toContain('Alpha');
    expect(body).not.toContain('Private Beta');
    expect(mocks.access).toHaveBeenCalledWith('alpha', 'reader', 'viewer');
  });

  it('blocks legacy default-project metadata without viewer access', async () => {
    mocks.role.mockResolvedValue([null, new Response('Denied', { status: 403 })]);
    const { GET } = await import('@/app/api/project/route');
    expect((await GET()).status).toBe(403);
    expect(mocks.get).not.toHaveBeenCalled();
    expect(mocks.role).toHaveBeenCalledWith('viewer', 'default');
  });
});
