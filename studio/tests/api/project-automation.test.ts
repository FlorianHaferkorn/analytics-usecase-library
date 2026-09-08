import {beforeEach,describe,expect,it,vi} from 'vitest';
const fake=vi.hoisted(()=>({role:vi.fn(),run:vi.fn(),deploy:vi.fn()}));
vi.mock('@/lib/auth/require-role',()=>({requireRole:fake.role}));
vi.mock('@/lib/bridge/project-automation',()=>({projectAutomation:fake.run}));
vi.mock('@/lib/bridge/project-deployment',()=>({projectDeployment:fake.deploy}));
const hash='a'.repeat(64);
const context={params:Promise.resolve({projectId:'alpha'})};
const post=(value:unknown)=>new Request('http://x/automation',{method:'POST',body:JSON.stringify(value)});
beforeEach(()=>{vi.clearAllMocks();fake.role.mockResolvedValue([{email:'operator@example.test'},null]);fake.run.mockResolvedValue({available:true,ok:true,value:{project_ref:'alpha',revision_hash:hash,generation_allowed:true}});fake.deploy.mockResolvedValue({available:true,ok:true,value:{plan_sha256:hash}});});

describe('Project automation API',()=>{
  it('authorizes before any project access',async()=>{
    fake.role.mockResolvedValue([null,new Response('denied',{status:403})]);
    const {GET,POST}=await import('@/app/api/projects/[projectId]/automation/route');
    expect((await GET(new Request('http://x/automation'),context)).status).toBe(403);
    expect((await POST(post({}),context)).status).toBe(403);expect(fake.run).not.toHaveBeenCalled();
  });
  it('requires a pinned hash and prevents shared caching',async()=>{
    const {GET}=await import('@/app/api/projects/[projectId]/automation/route');
    expect((await GET(new Request('http://x/automation'),context)).status).toBe(422);
    const response=await GET(new Request(`http://x/automation?revision=${hash}`),context);
    expect(fake.run).toHaveBeenCalledWith('alpha',hash);expect(response.headers.get('cache-control')).toBe('private, no-store');
  });
  it('requires selected outputs and confirmation and rejects actor spoofing or apply',async()=>{
    const {POST}=await import('@/app/api/projects/[projectId]/automation/route');
    for(const extra of [{targets:[]},{targets:['tenant_apply']},{targets:['architecture_bundle','architecture_bundle']},{confirmGeneration:false},{actor:'admin'}, {command:'fab rm'}]){
      const response=await POST(post({revisionHash:hash,targets:['architecture_bundle'],confirmGeneration:true,...extra}),context);
      expect(response.status).toBe(422);
    }
    expect(fake.run).not.toHaveBeenCalled();
  });
  it('passes only session identity to the bounded generation runner',async()=>{
    const {POST}=await import('@/app/api/projects/[projectId]/automation/route');
    const response=await POST(post({revisionHash:hash,targets:['architecture_bundle'],confirmGeneration:true}),context);
    expect(fake.role).toHaveBeenCalledWith('editor','alpha');
    expect(fake.run).toHaveBeenCalledWith('alpha',hash,{actor:'operator@example.test',targets:['architecture_bundle']});
    expect(response.headers.get('x-package-revision')).toBe(hash);
  });
  it('reads a stored run under viewer authorization without generating again',async()=>{
    const {GET}=await import('@/app/api/projects/[projectId]/automation/route');
    await GET(new Request(`http://x/automation?revision=${hash}&run=${hash}`),context);
    expect(fake.role).toHaveBeenCalledWith('viewer','alpha');
    expect(fake.run).toHaveBeenCalledWith('alpha',hash,undefined,hash);
    expect((await GET(new Request(`http://x/automation?revision=${hash}&run=../escape`),context)).status).toBe(422);
  });
  it('does not turn a stale release or failed generation into success',async()=>{
    fake.run.mockResolvedValue({available:true,ok:false,status:409,error:'HEAD changed'});
    const {POST}=await import('@/app/api/projects/[projectId]/automation/route');
    expect((await POST(post({revisionHash:hash,targets:['architecture_bundle'],confirmGeneration:true}),context)).status).toBe(409);
  });
});

describe('Read-only deployment preflight API',()=>{
  it('rejects apply and foreign plans without invoking the adapter',async()=>{
    const {POST}=await import('@/app/api/projects/[projectId]/deployment/route');
    for(const body of [{mode:'apply'}, {mode:'reconcile',plan:{project_ref:'beta',revision_hash:hash}}])
      expect((await POST(post({revisionHash:hash,observedState:{},...body}),context)).status).toBe(422);
    expect(fake.deploy).not.toHaveBeenCalled();
  });
  it('requires current release and pins target identity server-side',async()=>{
    const {POST}=await import('@/app/api/projects/[projectId]/deployment/route');
    const body={mode:'plan',revisionHash:hash,observedState:{complete:true},tenantId:'tenant',environment:'dev'};
    fake.run.mockResolvedValueOnce({ok:true,value:{generation_allowed:false}});
    expect((await POST(post(body),context)).status).toBe(409);expect(fake.deploy).not.toHaveBeenCalled();
    const response=await POST(post(body),context);
    expect(fake.deploy).toHaveBeenCalledWith('alpha','plan',{project_ref:'alpha',revision_hash:hash,tenant_id:'tenant',environment:'dev',observed_state:{complete:true}});
    expect(response.headers.get('cache-control')).toBe('private, no-store');
  });
  it('denies before parsing project evidence',async()=>{
    fake.role.mockResolvedValue([null,new Response('denied',{status:403})]);
    const {POST}=await import('@/app/api/projects/[projectId]/deployment/route');
    expect((await POST(post({}),context)).status).toBe(403);expect(fake.run).not.toHaveBeenCalled();expect(fake.deploy).not.toHaveBeenCalled();
  });
});
