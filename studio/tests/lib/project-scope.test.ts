import { beforeEach, describe, expect, it, vi } from 'vitest';
import { projectProjection } from '@/lib/project-package/projection';
import { surfaceScope, projectSurface } from '@/lib/project-package/view-policy';
import { useProjectStore } from '@/lib/store/project-store';
import type { PackageSnapshot } from '@/lib/bridge/project-package-repository';

const fake = vi.hoisted(() => ({ role: vi.fn(), load: vi.fn() }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: fake.role }));
vi.mock('@/lib/bridge/project-package-repository', () => ({ loadProjectPackage: fake.load }));

const hash = 'a'.repeat(64);
function snapshot(projectId = 'alpha'): PackageSnapshot {
  return { revision: { revision_hash: hash, package_id: 'package_alpha', project_ref: projectId, revision: 1, parent_revision_hash: null },
    files: [{ path: 'package.yaml', contentBase64: Buffer.from(JSON.stringify({ project_ref: projectId, revision: 1, state: 'working', modules: [{ module_type: 'plan', path: 'plan.json' }] })).toString('base64'), encoding: 'base64', sha256: hash, size: 1 },
    { path: 'plan.json', contentBase64: Buffer.from(JSON.stringify({ work_packages: [{id: 'one', title: 'Alpha only'}] })).toString('base64'), encoding: 'base64', sha256: hash, size: 1 }] };
}
beforeEach(() => { vi.clearAllMocks(); fake.role.mockResolvedValue([{ email: 'tester@example.org' }, null]); fake.load.mockResolvedValue({ ok: true, available: true, value: snapshot() }); });

describe('Project authority and isolation', () => {
  it('switching projects clears previous data and pinned revision', () => {
    useProjectStore.setState({ projectId: 'alpha', packageRevisionHash: hash, brackets: [{id:'old'}] as never, strategyAnchor: 'Alpha secret', selectedBracketId: 'old', pendingWizardDraft: {name:'old'} as never });
    useProjectStore.getState().setProjectId('beta');
    expect(useProjectStore.getState()).toMatchObject({ projectId: 'beta', dataScope: 'project', packageRevisionHash: null, brackets: [], strategyAnchor: '', selectedBracketId: null, pendingWizardDraft: null });
  });
  it('selecting the same project preserves its version', () => {
    useProjectStore.setState({projectId:'alpha', packageRevisionHash:hash});
    useProjectStore.getState().setProjectId('alpha');
    expect(useProjectStore.getState().packageRevisionHash).toBe(hash);
  });
  it('declares library assets, project drafts and administration independently', () => {
    expect(surfaceScope('/discover', 'library')).toBe('project');
    expect(surfaceScope('/architecture', 'library')).toBe('project');
    expect(surfaceScope('/engagement', 'library')).toBe('project');
    expect(surfaceScope('/library', 'project')).toBe('library');
    expect(surfaceScope('/organizations', 'project')).toBe('administration');
    expect(projectSurface('/compose')).toBe('unsupported');
  });
  it('projects only pinned modules, without library additions', () => {
    const result = projectProjection('alpha', snapshot());
    expect(result.modules).toHaveLength(1);
    expect(result.modules[0].data.work_packages).toEqual([{id:'one',title:'Alpha only'}]);
    expect(result.revision.revision_hash).toBe(hash);
  });
  it('rejects cross-project packages and missing declared modules', () => {
    expect(() => projectProjection('beta', snapshot())).toThrow('does not match');
    const broken = snapshot(); broken.files.pop();
    expect(() => projectProjection('alpha', broken)).toThrow('module missing');
  });
  it('authorizes before fetching a version', async () => {
    fake.role.mockResolvedValue([null, new Response('denied', {status:403})]);
    const { GET } = await import('@/app/api/projects/[projectId]/view/route');
    const result = await GET(new Request('http://x/view'), {params:Promise.resolve({projectId:'alpha'})});
    expect(result.status).toBe(403); expect(fake.load).not.toHaveBeenCalled();
  });
  it('binds the requested revision and forbids shared caching', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/view/route');
    const result = await GET(new Request(`http://x/view?revision=${hash}`), {params:Promise.resolve({projectId:'alpha'})});
    expect(result.status).toBe(200); expect(fake.load).toHaveBeenCalledWith('alpha', hash);
    expect(result.headers.get('Cache-Control')).toBe('private, no-store');
  });
  it('fails closed for invalid hash or a foreign snapshot', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/view/route');
    expect((await GET(new Request('http://x/view?revision=bad'), {params:Promise.resolve({projectId:'alpha'})})).status).toBe(422);
    fake.load.mockResolvedValue({ok:true, available:true, value:snapshot('beta')});
    expect((await GET(new Request('http://x/view'), {params:Promise.resolve({projectId:'alpha'})})).status).toBe(409);
  });
  it('legacy project writes never invoke global library handlers', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/core/brackets/route');
    const result = await POST(new Request('http://x/legacy', {method:'POST',body:'{}'}), {params:Promise.resolve({projectId:'alpha'})});
    expect(result.status).toBe(405); expect(fake.role).toHaveBeenCalledWith('editor','alpha'); expect(fake.load).not.toHaveBeenCalled();
  });
});
