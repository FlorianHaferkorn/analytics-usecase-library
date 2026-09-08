import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {ProjectAutomationPage} from '@/components/project/project-automation';
import {useProjectStore} from '@/lib/store/project-store';
const state=vi.hoisted(()=>({revision:'a'.repeat(64)}));
vi.mock('@/components/project/use-pinned-project',()=>({usePinnedProject:()=>({projectId:'alpha',projectName:'Alpha',revision:state.revision,value:{},latest:vi.fn(),retry:vi.fn()})}));
vi.mock('@/components/project/project-estimation',()=>({ProjectEstimation:()=> <div>Estimate fixture</div>}));
vi.mock('@/components/project/project-deployment',()=>({ProjectDeployment:()=> <div>Deployment fixture</div>}));
const status=()=>({project_ref:'alpha',revision_hash:state.revision,generation_allowed:true,stages:[],automation_gaps:['Security adapter required'],targets:[{id:'architecture_bundle',label:'Architecture bundle',status:'ready',reason:'Recorded definitions'},{id:'fabric_workspace_requests',label:'Workspaces',status:'blocked',reason:'Missing workspace contract'}],latest_run:null});
beforeEach(()=>{state.revision='a'.repeat(64);useProjectStore.setState({projectId:'alpha',packageRevisionHash:state.revision});vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>status()})));});
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
describe('Automation project boundaries and explicit scope',()=>{
  it('requires target selection and confirmation and clears both on revision change',async()=>{
    const {rerender}=render(<ProjectAutomationPage />);
    const generate=await screen.findByRole('button',{name:'Run selected generation'});
    expect((generate as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole('checkbox',{name:/Architecture bundle/}));
    fireEvent.click(screen.getByRole('checkbox',{name:/Generate only these outputs/}));
    expect((generate as HTMLButtonElement).disabled).toBe(false);
    expect((screen.getByRole('checkbox',{name:/Workspaces/}) as HTMLInputElement).disabled).toBe(true);
    state.revision='b'.repeat(64);useProjectStore.setState({packageRevisionHash:state.revision});rerender(<ProjectAutomationPage />);
    await screen.findByRole('button',{name:'Run selected generation'});
    expect((screen.getByRole('checkbox',{name:/Generate only these outputs/}) as HTMLInputElement).checked).toBe(false);
  });
  it('rejects foreign status and blocks generation without release',async()=>{
    vi.mocked(fetch).mockResolvedValueOnce({ok:true,json:async()=>({...status(),project_ref:'beta'})} as Response);
    const view=render(<ProjectAutomationPage />);
    await screen.findByText('Automation version mismatch');expect(screen.queryByRole('button',{name:'Run selected generation'})).toBeNull();
    view.unmount();vi.mocked(fetch).mockResolvedValue({ok:true,json:async()=>({...status(),generation_allowed:false})} as Response);
    render(<ProjectAutomationPage />);await screen.findByRole('button',{name:'Run selected generation'});
    fireEvent.click(screen.getByRole('checkbox',{name:/Architecture bundle/}));
    expect((screen.getByRole('checkbox',{name:/Generate only these outputs/}) as HTMLInputElement).disabled).toBe(true);
  });
  it('submits pinned targets and never exposes tenant apply',async()=>{
    render(<ProjectAutomationPage />);await screen.findByRole('button',{name:'Run selected generation'});
    fireEvent.click(screen.getByRole('checkbox',{name:/Architecture bundle/}));fireEvent.click(screen.getByRole('checkbox',{name:/Generate only these outputs/}));
    vi.mocked(fetch).mockResolvedValueOnce({ok:false,json:async()=>({error:{message:'Stale release'}})} as Response);
    fireEvent.click(screen.getByRole('button',{name:'Run selected generation'}));
    await waitFor(()=>expect(screen.getByRole('status').textContent).toBe('Stale release'));
    const [,init]=vi.mocked(fetch).mock.calls.find(([,init])=>init?.method==='POST')!;
    expect(JSON.parse(init!.body as string)).toEqual({revisionHash:state.revision,targets:['architecture_bundle'],confirmGeneration:true});
    expect(screen.queryByRole('button',{name:/apply|deploy now/i})).toBeNull();
  });
});
