'use client';
import {useEffect,useRef,useState} from 'react';
import {StudioButton,StudioPanel} from '@/components/ui/studio-page';
import type {DeploymentPlan,DeploymentReadback} from '@/lib/bridge/project-deployment';
import styles from './project-automation.module.css';
import {ProjectRunner} from './project-runner';

export function ProjectDeployment({projectId,revision}:{projectId:string;revision:string}) {
  const [tenant,setTenant]=useState('');const [environment,setEnvironment]=useState('');
  const [evidence,setEvidence]=useState<Record<string,unknown>|null>(null);const [filename,setFilename]=useState('');
  const [plan,setPlan]=useState<DeploymentPlan|null>(null);const [readback,setReadback]=useState<DeploymentReadback|null>(null);
  const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  const sequence=useRef(0);
  useEffect(()=>()=>{sequence.current+=1;},[]);
  function invalidate(){sequence.current+=1;setPlan(null);setReadback(null);setBusy(false);setError('');}
  async function load(file:File|undefined){
    sequence.current+=1;const request=sequence.current;setEvidence(null);setReadback(null);setFilename('');setBusy(false);setError('');
    if (!file) return;
    try {
      if(file.size>1_000_000) throw new Error('Evidence file must be smaller than 1 MB');
      const data=JSON.parse(await file.text());
      if(!data || Array.isArray(data) || typeof data!=='object' || !data.tenant_id || !data.observed_at) throw new Error('A workspace observation JSON document is required');
      if(sequence.current===request){setEvidence(data);setFilename(file.name);}
    } catch(e){if(sequence.current===request)setError(e instanceof Error?e.message:'Invalid evidence');}
  }
  async function inspect(mode:'plan'|'reconcile'){
    if(!evidence || busy || (mode==='reconcile'&&!plan)) return;
    const request=++sequence.current;setBusy(true);setError('');setReadback(null);
    if(mode==='plan')setPlan(null);
    try{
      const response=await fetch(`/api/projects/${encodeURIComponent(projectId)}/deployment`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({mode,revisionHash:revision,observedState:evidence,...(mode==='plan'?{tenantId:tenant,environment}:{plan})})});
      const value=await response.json();
      if(!response.ok)throw new Error(value.error?.message??'Deployment preflight did not complete');
      if(value.project_ref!==projectId || value.revision_hash!==revision)throw new Error('Deployment project version mismatch');
      if(sequence.current===request){if(mode==='plan')setPlan(value);else setReadback(value);}
    }catch(e){if(sequence.current===request)setError(e instanceof Error?e.message:'Preflight failed');}
    finally{if(sequence.current===request)setBusy(false);}
  }
  function download(){
    if(!plan)return;
    const url=URL.createObjectURL(new Blob([JSON.stringify({plan,readback},null,2)],{type:'application/json'}));
    const link=document.createElement('a');link.href=url;link.download=`${projectId}-workspace-plan-${plan.plan_sha256.slice(0,12)}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  return <ProjectRunner key={`${projectId}:${revision}`} projectId={projectId} revision={revision} plan={plan}>
    <StudioPanel title="Workspace deployment preflight" description="Compare the released workspace contract with explicit target evidence. Planning does not create, update or delete tenant resources.">
      <p className={styles.note}>Execution requires the separately approved plan and protected host below. Uploaded evidence is checked for freshness and consistency; this is not an independent live tenant check.</p>
      <div className={styles.inputs}>
        <label>Target tenant ID<input value={tenant} onChange={e=>{invalidate();setTenant(e.target.value);}} placeholder="Tenant UUID" /></label>
        <label>Environment<input value={environment} onChange={e=>{invalidate();setEnvironment(e.target.value);}} placeholder="Exact environment from the Package" /></label>
        <label>Workspace observation JSON<input type="file" accept=".json,application/json" onChange={e=>void load(e.target.files?.[0])} /></label>
      </div>
      {filename&&<p className={styles.note}>Loaded evidence: {filename}</p>}
      <details className={styles.fileDetails}><summary>Evidence requirements</summary><p>The observation must contain tenant and principal IDs, a timezone-aware timestamp less than 15 minutes old, a complete principal-visible workspace inventory, and explicit permission evidence for creation and capacity/domain assignment. An empty visible inventory is not proof that a tenant contains no workspaces.</p><p>Use the trusted runner’s observation format. Do not put access tokens or client secrets in this file. Import a fresh observation after execution to compare it with the same plan.</p></details>
      <div className={styles.actions}><StudioButton disabled={busy||!evidence||!tenant||!environment} onClick={()=>inspect('plan')}>{busy?'Checking evidence…':'Build workspace plan'}</StudioButton>{plan&&<><StudioButton disabled={busy||!evidence} onClick={()=>inspect('reconcile')}>Compare latest evidence</StudioButton><StudioButton onClick={download}>Download plan and readback</StudioButton></>}</div>
      {error&&<p role="alert">{error}</p>}
    </StudioPanel>
    {plan&&<StudioPanel title="Planned workspace operations" description={plan.workspace_apply_ready?'Workspace preflight passed. This is not whole-project deployment readiness or apply approval.':'Resolve conflicts or missing evidence before applying workspace changes.'}>
      <p className={styles.note}>Target: {plan.tenant_id} · {plan.environment} · Plan {plan.plan_sha256.slice(0,12)}</p>
      <div className={styles.tableWrap}><table><thead><tr><th>Workspace</th><th>Operation</th><th>Reason</th></tr></thead><tbody>{plan.operations.map(operation=><tr key={operation.id}><td>{operation.desired.name}</td><td>{operation.action==='noop'?'No change':operation.action}</td><td>{operation.reason}</td></tr>)}</tbody></table></div>
      {readback&&<div role="status"><h3>{readback.workspace_match?'Workspace contracts match the supplied evidence':'Workspace differences found'}</h3><ul>{readback.results.map(result=><li key={result.id}>{result.id}: {result.state}</li>)}</ul><p>Item definitions, data quality, security and business acceptance are not verified by this comparison.</p></div>}
      <details className={styles.fileDetails}><summary>Adapter coverage and exclusions</summary><ul className={styles.gaps}>{plan.capabilities.map(capability=><li key={capability.family}><strong>{capability.family}: {capability.status}</strong> · {capability.reason}</li>)}</ul></details>
    </StudioPanel>}
  </ProjectRunner>;
}
