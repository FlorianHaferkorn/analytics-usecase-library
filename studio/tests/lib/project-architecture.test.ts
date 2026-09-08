import { beforeEach, describe, expect, it, vi } from 'vitest';
const fake = vi.hoisted(() => ({ role: vi.fn(), compile: vi.fn() }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: fake.role }));
vi.mock('@/lib/bridge/project-architecture', () => ({ projectArchitecture: fake.compile }));
const hash = 'a'.repeat(64);
const context = { params: Promise.resolve({ projectId: 'project_demo' }) };
beforeEach(() => { vi.clearAllMocks(); fake.role.mockResolvedValue([{email:'test@example.test'},null]); fake.compile.mockResolvedValue({available:true,ok:true,value:{project_ref:'project_demo',revision_hash:hash}}); });
describe('Project architecture authority', () => {
  it('denies before loading customer architecture', async () => {
    fake.role.mockResolvedValue([null,new Response('denied',{status:403})]);
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/route');
    expect((await GET(new Request('http://x/architecture'),context)).status).toBe(403);
    expect(fake.compile).not.toHaveBeenCalled();
  });
  it('pins a revision and prevents shared caching', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/architecture/route');
    const result = await GET(new Request(`http://x/architecture?revision=${hash}`),context);
    expect(fake.compile).toHaveBeenCalledWith('project_demo',hash);
    expect(result.headers.get('cache-control')).toBe('private, no-store');
  });
  it('requires explicit supported target confirmation', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/architecture/route');
    for (const body of [{revisionHash:hash,target:'architecture_bundle'}, {revisionHash:hash,target:'tenant_apply',confirmGeneration:true}]) {
      expect((await POST(new Request('http://x/architecture',{method:'POST',body:JSON.stringify(body)}),context)).status).toBe(422);
    }
    expect(fake.compile).not.toHaveBeenCalled();
  });
  it('uses editor rights and existing release attestation without granting one', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/architecture/route');
    const result = await POST(new Request('http://x/architecture',{method:'POST',body:JSON.stringify({revisionHash:hash,target:'fabric_workspace_requests',confirmGeneration:true})}),context);
    expect(fake.role).toHaveBeenCalledWith('editor','project_demo');
    expect(fake.compile).toHaveBeenCalledWith('project_demo',hash,'fabric_workspace_requests');
    expect(result.headers.get('content-disposition')).toContain('attachment');
    expect(result.headers.get('x-package-revision')).toBe(hash);
  });
  it('does not convert blocked generation into a preview', async () => {
    fake.compile.mockResolvedValue({available:true,ok:false,status:409,error:'Release blocked'});
    const { POST } = await import('@/app/api/projects/[projectId]/architecture/route');
    expect((await POST(new Request('http://x/architecture',{method:'POST',body:JSON.stringify({revisionHash:hash,target:'architecture_bundle',confirmGeneration:true})}),context)).status).toBe(409);
  });
});
