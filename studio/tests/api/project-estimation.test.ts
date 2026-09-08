import { beforeEach, describe, expect, it, vi } from 'vitest';
const fake = vi.hoisted(() => ({role:vi.fn(),estimate:vi.fn()}));
vi.mock('@/lib/auth/require-role',() => ({requireRole:fake.role}));
vi.mock('@/lib/bridge/project-estimation',() => ({projectEstimation:fake.estimate}));
const hash = 'a'.repeat(64);
const context = {params:Promise.resolve({projectId:'project_demo'})};
beforeEach(() => {vi.clearAllMocks();fake.role.mockResolvedValue([{email:'test@example.test'},null]);fake.estimate.mockResolvedValue({ok:true,available:true,value:{project_ref:'project_demo',revision_hash:hash}});});
describe('Private estimate preview',() => {
  it('checks project editor access before accepting rates',async () => {
    fake.role.mockResolvedValue([null,new Response('denied',{status:403})]);
    const {POST} = await import('@/app/api/projects/[projectId]/estimation/route');
    expect((await POST(new Request('http://x',{method:'POST',body:'{}'}),context)).status).toBe(403);
    expect(fake.role).toHaveBeenCalledWith('editor','project_demo');
    expect(fake.estimate).not.toHaveBeenCalled();
  });
  it('requires a pinned revision',async () => {
    const {POST} = await import('@/app/api/projects/[projectId]/estimation/route');
    expect((await POST(new Request('http://x',{method:'POST',body:JSON.stringify({scenario:{}})}),context)).status).toBe(422);
    expect(fake.estimate).not.toHaveBeenCalled();
  });
  it('never caches rates and pins the calculation',async () => {
    const {POST} = await import('@/app/api/projects/[projectId]/estimation/route');
    const scenario = {currency:'EUR'};
    const response = await POST(new Request('http://x',{method:'POST',body:JSON.stringify({revisionHash:hash,scenario})}),context);
    expect(response.status).toBe(200);
    expect(response.headers.get('cache-control')).toBe('private, no-store');
    expect(fake.estimate).toHaveBeenCalledWith('project_demo',hash,scenario);
  });
  it('reports calculation errors rather than inventing values',async () => {
    fake.estimate.mockResolvedValue({available:true,ok:false,status:422,error:'Mixed currencies'});
    const {POST} = await import('@/app/api/projects/[projectId]/estimation/route');
    expect((await POST(new Request('http://x',{method:'POST',body:JSON.stringify({revisionHash:hash,scenario:{}})}),context)).status).toBe(422);
  });
});
