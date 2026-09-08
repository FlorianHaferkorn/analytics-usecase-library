import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {ProjectArchitecture} from '@/components/project/project-architecture';

const state = vi.hoisted(() => ({revision:'a'.repeat(64)}));
vi.mock('@/components/project/use-pinned-project',() => ({usePinnedProject:() => ({projectId:'alpha',projectName:'Alpha',revision:state.revision,error:undefined,latest:vi.fn(),retry:vi.fn()})}));
vi.mock('@/components/canvas/custom-canvas',() => ({CustomCanvas:() => <div>Graph fixture</div>}));
beforeEach(() => {
  state.revision = 'a'.repeat(64);
  vi.stubGlobal('fetch',vi.fn(async () => ({ok:true,json:async () => ({project_ref:'alpha',revision_hash:state.revision,graph:{nodes:[],edges:[]},architecture:null,use_cases:[],readiness:{release_ready:true,blockers:[],apply_ready:false},outputs:[{id:'architecture_bundle',label:'Architecture bundle',status:'ready',reason:'Recorded inputs'}]})})));
});
afterEach(() => {cleanup();vi.unstubAllGlobals();});

describe('Architecture generation confirmation',() => {
  it('binds the confirmation to the exact project revision',async () => {
    const {rerender} = render(<ProjectArchitecture />);
    fireEvent.click(await screen.findByRole('button',{name:'Build outputs'}));
    fireEvent.click(screen.getByRole('checkbox'));
    expect((screen.getByRole('button',{name:'Generate architecture bundle'}) as HTMLButtonElement).disabled).toBe(false);
    state.revision = 'b'.repeat(64);
    rerender(<ProjectArchitecture />);
    await screen.findByRole('button',{name:'Generate architecture bundle'});
    expect((screen.getByRole('checkbox') as HTMLInputElement).checked).toBe(false);
    expect((screen.getByRole('button',{name:'Generate architecture bundle'}) as HTMLButtonElement).disabled).toBe(true);
  });

  it('rejects architecture from a foreign project instead of displaying it',async () => {
    vi.mocked(fetch).mockResolvedValue({ok:true,json:async () => ({project_ref:'beta',revision_hash:state.revision})} as Response);
    render(<ProjectArchitecture />);
    await waitFor(() => expect(screen.getByText('Architecture project or revision mismatch')).toBeTruthy());
    expect(screen.queryByRole('button',{name:'Build outputs'})).toBeNull();
  });
});
