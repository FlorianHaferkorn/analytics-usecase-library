import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {ProjectEstimation,restoreEstimateInputs} from '@/components/project/project-estimation';

const revisionHash = 'a'.repeat(64);
const result = {project_ref:'alpha',revision_hash:revisionHash,currency:'EUR',totals:{cost:'10.00',revenue:'20.00',contribution:'10.00',margin_percent:'50.0000',buffered_hours:'1.0000',minimum_workdays:'0.1250'},people:[],roles:[],warnings:[],limitations:[]};
const inputs = {currency:'EUR',planning_workdays:'10',contingency_percent:'0',people:[{id:'p1',name:'Consultant',hours_per_day:'8',availability_percent:'50'}],assignments:[{id:'a1',person_id:'p1',role:'Engineer',effort_hours:'40',cost_per_hour:'50',sell_per_hour:'100',currency:'EUR'}]};
beforeEach(() => {vi.stubGlobal('fetch',vi.fn(async () => ({ok:true,json:async () => result})));});
afterEach(() => {cleanup();vi.unstubAllGlobals();});
function submit() {fireEvent.submit(screen.getByRole('button',{name:'Calculate scenario'}).closest('form')!);}

describe('Private estimate scenario',() => {
  it('has no invented commercial defaults and clears rates across revisions',() => {
    const {rerender} = render(<ProjectEstimation projectId="alpha" revisionHash={revisionHash} />);
    const rate = screen.getByLabelText('Work 1 sell rate / hour') as HTMLInputElement;
    expect(rate.value).toBe('');
    fireEvent.change(rate,{target:{value:'125'}});
    rerender(<ProjectEstimation projectId="alpha" revisionHash={'b'.repeat(64)} />);
    expect((screen.getByLabelText('Work 1 sell rate / hour') as HTMLInputElement).value).toBe('');
  });
  it('invalidates calculated outputs when inputs change',async () => {
    render(<ProjectEstimation projectId="alpha" revisionHash={revisionHash} />);
    submit();
    await screen.findByRole('button',{name:'Download private scenario'});
    fireEvent.change(screen.getByLabelText('Currency code'),{target:{value:'USD'}});
    expect(screen.queryByRole('button',{name:'Download private scenario'})).toBeNull();
  });
  it('rejects cross-project responses',async () => {
    vi.mocked(fetch).mockResolvedValue({ok:true,json:async () => ({...result,project_ref:'beta'})} as Response);
    render(<ProjectEstimation projectId="alpha" revisionHash={revisionHash} />);
    submit();
    await screen.findByRole('alert');
    expect(screen.getByText('Project version mismatch')).toBeTruthy();
    expect(screen.queryByRole('button',{name:'Download private scenario'})).toBeNull();
  });
  it('ignores late calculations after edits',async () => {
    let resolve!: (response: Response) => void;
    vi.mocked(fetch).mockImplementation(() => new Promise<Response>(accept => {resolve=accept;}));
    render(<ProjectEstimation projectId="alpha" revisionHash={revisionHash} />);
    submit();
    fireEvent.change(screen.getByLabelText('Currency code'),{target:{value:'EUR'}});
    resolve({ok:true,json:async () => result} as Response);
    await waitFor(() => expect(screen.getByRole('button',{name:'Calculate scenario'})).toBeTruthy());
    expect(screen.queryByRole('button',{name:'Download private scenario'})).toBeNull();
  });
  it('restores private inputs but never trusts downloaded totals',async () => {
    render(<ProjectEstimation projectId="alpha" revisionHash={revisionHash} />);
    const file = {size:500,text:async () => JSON.stringify({...result,inputs})};
    fireEvent.change(screen.getByLabelText(/Restore private scenario/),{target:{files:[file]}});
    await screen.findByText(/Private inputs restored/);
    expect((screen.getByLabelText('Work 1 sell rate / hour') as HTMLInputElement).value).toBe('100');
    expect(screen.queryByRole('button',{name:'Download private scenario'})).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
  });
  it('rejects files from another project or revision',() => {
    expect(() => restoreEstimateInputs(JSON.stringify({...result,inputs}),'beta',revisionHash)).toThrow('different project or revision');
    expect(() => restoreEstimateInputs(JSON.stringify({...result,inputs}),'alpha','b'.repeat(64))).toThrow('different project or revision');
  });
  it('rejects oversized files, malformed fields and unknown resources',() => {
    expect(() => restoreEstimateInputs(' '.repeat(1_048_577),'alpha',revisionHash)).toThrow('1 MB');
    expect(() => restoreEstimateInputs(JSON.stringify({...result,inputs:{...inputs,people:null}}),'alpha',revisionHash)).toThrow('structure');
    expect(() => restoreEstimateInputs(JSON.stringify({...result,inputs:{...inputs,assignments:[{...inputs.assignments[0],person_id:'foreign'}]}}),'alpha',revisionHash)).toThrow('resource references');
  });
});
