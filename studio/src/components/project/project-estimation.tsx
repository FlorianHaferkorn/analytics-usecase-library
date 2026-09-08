'use client';

import { useEffect, useRef, useState } from 'react';
import { StudioButton, StudioPanel } from '@/components/ui/studio-page';
import type { EstimateResult, EstimateScenario } from '@/lib/bridge/project-estimation';
import styles from './project-estimation.module.css';

type Props = {projectId: string; revisionHash: string};
const empty = (): EstimateScenario => ({currency:'',planning_workdays:'',contingency_percent:'',people:[{id:'person_1',name:'',hours_per_day:'',availability_percent:''}],assignments:[{id:'work_1',person_id:'person_1',role:'',effort_hours:'',cost_per_hour:'',sell_per_hour:'',currency:''}]});

/** Restores inputs only. Previously calculated outputs and approval-like metadata are not trusted. */
export function restoreEstimateInputs(text: string, projectId: string, revisionHash: string): EstimateScenario {
  if (text.length > 1_048_576) throw new Error('Private scenario exceeds the 1 MB limit');
  const saved = JSON.parse(text);
  if (!saved || saved.project_ref !== projectId || saved.revision_hash !== revisionHash) throw new Error('This private scenario belongs to a different project or revision');
  const input = saved.inputs;
  const exact = (value: unknown, fields: string[]) => value !== null && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).sort().join('|') === [...fields].sort().join('|');
  if (!exact(input,['currency','planning_workdays','contingency_percent','people','assignments']) || typeof input.currency !== 'string' || typeof input.planning_workdays !== 'string' || typeof input.contingency_percent !== 'string'
    || !Array.isArray(input.people) || input.people.length < 1 || input.people.length > 200 || !Array.isArray(input.assignments) || input.assignments.length < 1 || input.assignments.length > 1000) throw new Error('Unsupported private scenario input structure');
  const peopleFields = ['id','name','hours_per_day','availability_percent'];
  const workFields = ['id','person_id','role','effort_hours','cost_per_hour','sell_per_hour','currency'];
  for (const [items,fields] of [[input.people,peopleFields],[input.assignments,workFields]] as const) {
    if (!items.every((item: unknown) => exact(item,fields) && Object.values(item as object).every(value => typeof value === 'string' && value.length <= 160))) throw new Error('Unsupported private scenario field values');
  }
  const ids = new Set(input.people.map((person: {id: string}) => person.id));
  if (ids.size !== input.people.length || new Set(input.assignments.map((item: {id: string}) => item.id)).size !== input.assignments.length || !input.assignments.every((item: {person_id: string}) => ids.has(item.person_id))) throw new Error('Private scenario has duplicate or unknown resource references');
  return input as EstimateScenario;
}

/** Remount on project/revision change: private scenario values never cross that boundary. */
export function ProjectEstimation(props: Props) {
  return <EstimateForm key={`${props.projectId}:${props.revisionHash}`} {...props} />;
}

function EstimateForm({projectId,revisionHash}: Props) {
  const [scenario,setScenario] = useState<EstimateScenario>(empty);
  const [result,setResult] = useState<EstimateResult | null>(null);
  const [error,setError] = useState('');
  const [restored,setRestored] = useState(false);
  const [busy,setBusy] = useState(false);
  const sequence = useRef(0);
  useEffect(() => () => { sequence.current += 1; }, []);
  const change = (next: EstimateScenario) => {sequence.current += 1;setScenario(next);setResult(null);setError('');setBusy(false);};
  const field = (label: string, value: string, onChange: (value: string) => void, numeric = false) => <label key={label} className={styles.field}>{label}<input required value={value} type={numeric ? 'number' : 'text'} min={numeric ? '0' : undefined} step={numeric ? 'any' : undefined} onChange={e => onChange(e.target.value)} /></label>;
  async function calculate(event: React.FormEvent) {
    event.preventDefault();
    const request = ++sequence.current;
    setBusy(true);setError('');setResult(null);
    try {
      const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/estimation`, {method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({revisionHash,scenario})});
      const value = await response.json();
      if (!response.ok) throw new Error(value.error?.message || 'Calculation failed');
      if (value.project_ref !== projectId || value.revision_hash !== revisionHash) throw new Error('Project version mismatch');
      if (sequence.current === request) setResult(value);
    } catch (cause) {if (sequence.current === request) setError(cause instanceof Error ? cause.message : 'Calculation failed');}
    finally {if (sequence.current === request) setBusy(false);}
  }
  function download() {
    if (!result) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));
    const link = document.createElement('a');link.href=url;link.download=`${projectId}-private-estimate-${revisionHash.slice(0,12)}.json`;link.click();URL.revokeObjectURL(url);
  }
  async function restore(file: File | undefined) {
    if (!file) return;
    const request = ++sequence.current;
    setBusy(false);setResult(null);setError('');setRestored(false);
    try {
      if (file.size > 1_048_576) throw new Error('Private scenario exceeds the 1 MB limit');
      const inputs = restoreEstimateInputs(await file.text(),projectId,revisionHash);
      if (sequence.current === request) {setScenario(inputs);setRestored(true);}
    } catch (cause) {if (sequence.current === request) setError(cause instanceof Error ? cause.message : 'Unable to restore private scenario');}
  }
  return <StudioPanel title="Effort, staffing and commercial scenario" description="Calculate from explicit rates and availability. This private preview does not change the project package, an offer or a staffing approval.">
    <form className={styles.form} onSubmit={calculate}>
      <p className={styles.note}>Unsaved scenario for revision {revisionHash.slice(0,12)}. Values reset when the project or revision changes. Download the result to retain it. Do not include confidential rates in customer-facing exports.</p>
      <label className={styles.field}>Restore private scenario (same project and revision, max. 1 MB)<input type="file" accept=".json,application/json" onChange={event => {void restore(event.target.files?.[0]);event.target.value='';}} /></label>
      {restored && <p role="status">Private inputs restored. Calculate again to validate them and refresh the results.</p>}
      <div className={styles.fields}>
        {field('Currency code',scenario.currency,v => change({...scenario,currency:v.toUpperCase(),assignments:scenario.assignments.map(a => ({...a,currency:v.toUpperCase()}))}))}
        {field('Planning horizon (working days)',scenario.planning_workdays,v => change({...scenario,planning_workdays:v}),true)}
        {field('Effort contingency (%)',scenario.contingency_percent,v => change({...scenario,contingency_percent:v}),true)}
      </div>
      <fieldset className={styles.group}><legend>Named resource capacity</legend>
        {scenario.people.map((person,index) => <div key={person.id} className={styles.row}>
          <div className={styles.fields}>
            {field(`Person ${index+1} name`,person.name,v => change({...scenario,people:scenario.people.map(p => p.id === person.id ? {...p,name:v} : p)}))}
            {field(`Person ${index+1} hours / day`,person.hours_per_day,v => change({...scenario,people:scenario.people.map(p => p.id === person.id ? {...p,hours_per_day:v} : p)}),true)}
            {field(`Person ${index+1} availability (%)`,person.availability_percent,v => change({...scenario,people:scenario.people.map(p => p.id === person.id ? {...p,availability_percent:v} : p)}),true)}
          </div>
          {scenario.people.length > 1 && <StudioButton type="button" disabled={scenario.assignments.some(a => a.person_id === person.id)} onClick={() => change({...scenario,people:scenario.people.filter(p => p.id !== person.id)})}>Remove person {index+1}</StudioButton>}
        </div>)}
        <StudioButton type="button" onClick={() => change({...scenario,people:[...scenario.people,{id:crypto.randomUUID(),name:'',hours_per_day:'',availability_percent:''}]})}>Add person</StudioButton>
      </fieldset>
      <fieldset className={styles.group}><legend>Work and explicit hourly rates</legend>
        {scenario.assignments.map((item,index) => <div key={item.id} className={styles.row}>
          <div className={styles.fields}>
            <label className={styles.field}>Work {index+1} person<select value={item.person_id} onChange={e => change({...scenario,assignments:scenario.assignments.map(a => a.id === item.id ? {...a,person_id:e.target.value} : a)})}>{scenario.people.map((p,i) => <option key={p.id} value={p.id}>{p.name || `Person ${i+1}`}</option>)}</select></label>
            {(['role','effort_hours','cost_per_hour','sell_per_hour'] as const).map(key => field(`Work ${index+1} ${{role:'role',effort_hours:'effort (hours)',cost_per_hour:'cost / hour',sell_per_hour:'sell rate / hour'}[key]}`,item[key],v => change({...scenario,assignments:scenario.assignments.map(a => a.id === item.id ? {...a,[key]:v} : a)}),key !== 'role'))}
          </div>
          {scenario.assignments.length > 1 && <StudioButton type="button" onClick={() => change({...scenario,assignments:scenario.assignments.filter(a => a.id !== item.id)})}>Remove work {index+1}</StudioButton>}
        </div>)}
        <StudioButton type="button" onClick={() => change({...scenario,assignments:[...scenario.assignments,{id:crypto.randomUUID(),person_id:scenario.people[0].id,role:'',effort_hours:'',cost_per_hour:'',sell_per_hour:'',currency:scenario.currency}]})}>Add work assignment</StudioButton>
      </fieldset>
      <div className={styles.actions}><StudioButton type="submit" disabled={busy}>{busy ? 'Calculating…' : 'Calculate scenario'}</StudioButton>{result && <StudioButton type="button" onClick={download}>Download private scenario</StudioButton>}</div>
      {error && <p role="alert">{error}</p>}
    </form>
    {result && <div className={styles.results} aria-live="polite">
      <dl className={styles.metrics}>{[['Buffered effort',`${result.totals.buffered_hours} hours`],['Delivery cost',`${result.totals.cost} ${result.currency}`],['Rate-based revenue',`${result.totals.revenue} ${result.currency}`],['Contribution',`${result.totals.contribution} ${result.currency}`],['Margin',result.totals.margin_percent === null ? 'Not defined (zero revenue)' : `${result.totals.margin_percent}%`],['Capacity lower bound',result.totals.minimum_workdays === null ? 'Infeasible: assigned person has no capacity' : `${result.totals.minimum_workdays} working days`]].map(([label,value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
      {result.warnings.length > 0 && <ul>{result.warnings.map(w => <li key={w}>{w}</li>)}</ul>}
      <div className={styles.tableWrap}><table><caption>Resource allocation in the planning horizon</caption><thead><tr><th>Person</th><th>Effort / available hours</th><th>Allocation</th><th>Cost</th><th>Revenue</th></tr></thead><tbody>{result.people.map(p => <tr key={p.id}><td>{p.name}</td><td>{p.buffered_hours} / {p.capacity_hours}</td><td>{p.overallocated ? 'Overallocated' : 'Within capacity'}</td><td>{p.cost}</td><td>{p.revenue}</td></tr>)}</tbody></table></div>
      <div className={styles.tableWrap}><table><caption>Totals by role ({result.currency})</caption><thead><tr><th>Role</th><th>Buffered hours</th><th>Cost</th><th>Revenue</th></tr></thead><tbody>{result.roles.map(r => <tr key={r.role}><td>{r.role}</td><td>{r.buffered_hours}</td><td>{r.cost}</td><td>{r.revenue}</td></tr>)}</tbody></table></div>
      <ul className={styles.note}>{result.limitations.map(l => <li key={l}>{l}</li>)}</ul>
    </div>}
  </StudioPanel>;
}
