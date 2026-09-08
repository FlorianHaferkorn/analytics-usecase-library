'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import dagre from '@dagrejs/dagre';
import { CustomCanvas } from '@/components/canvas/custom-canvas';
import type { CanvasNode, CanvasEdge, NodeKind } from '@/components/canvas/canvas-types';
import { StudioButton, StudioEmptyState, StudioPageHeader, StudioPanel, StudioSegmentedControl } from '@/components/ui/studio-page';
import { usePinnedProject } from './use-pinned-project';
import type { ProjectArchitecture as ArchitectureView } from '@/lib/bridge/project-architecture';
import styles from './project-architecture.module.css';
const title = (key:string) => key.replaceAll('_',' ').replace(/^./,s => s.toUpperCase());
function ContractValue({value}:{value:unknown}) {
  if (value == null || value === '') return <span className={styles.note}>Not recorded</span>;
  if (typeof value === 'boolean') return <span>{value ? 'Yes' : 'No'}</span>;
  if (Array.isArray(value)) return value.length ? <ul className={styles.values}>{value.map((v,i) => <li key={i}><ContractValue value={v} /></li>)}</ul> : <span className={styles.note}>None recorded</span>;
  if (typeof value === 'object') return <dl className={styles.facts}>{Object.entries(value).map(([key,v]) => <div key={key}><dt>{title(key)}</dt><dd>{typeof v === 'object' && v !== null ? <details><summary>Show {title(key).toLowerCase()}</summary><ContractValue value={v} /></details> : <ContractValue value={v} />}</dd></div>)}</dl>;
  return <span>{String(value)}</span>;
}
const kinds:Record<string,NodeKind> = {source:'source',data_product:'data_product',transformation:'transformation',reference_report:'reference_report',workspace:'workspace',domain:'domain',native_item:'native_item'};
type Tab = 'graph'|'contracts'|'outputs';

export function ProjectArchitecture() {
  const {projectId,projectName,revision,error:packageError,latest,retry} = usePinnedProject();
  const [loaded,setLoaded] = useState<{key:string;view?:ArchitectureView;error?:string}|null>(null);
  const [attempt,setAttempt] = useState(0);
  const [tab,setTab] = useState<Tab>('graph');
  const [useCase,setUseCase] = useState('');
  const [references,setReferences] = useState(false);
  const [lineage,setLineage] = useState(false);
  const [confirmedIdentity,setConfirmedIdentity] = useState<string|null>(null);
  const [busyIdentity,setBusyIdentity] = useState<string|null>(null);
  const [message,setMessage] = useState<{key:string;text:string}|null>(null);
  const identity = `${projectId}:${revision}`;
  const confirm = confirmedIdentity === identity;
  const busy = busyIdentity === identity;
  const notice = message?.key === identity ? message.text : '';
  const active = useRef(identity);
  useEffect(() => {active.current = identity;return () => {active.current = '';};},[identity]);
  const view = loaded?.key === identity ? loaded.view : undefined;
  const currentUseCase = view?.use_cases.some(uc => uc.id === useCase) ? useCase : '';
  const error = packageError ?? (loaded?.key === identity ? loaded.error : undefined);
  useEffect(() => {
    if (!revision) return;
    const controller = new AbortController();
    void fetch(`/api/projects/${encodeURIComponent(projectId)}/architecture?revision=${revision}`,{cache:'no-store',signal:controller.signal}).then(async response => {
      const data = await response.json();
      if (!response.ok) throw new Error(data.error?.message ?? 'Architecture unavailable');
      const next = data as ArchitectureView;
      if (next.project_ref !== projectId || next.revision_hash !== revision) throw new Error('Architecture project or revision mismatch');
      if (!controller.signal.aborted) setLoaded({key:identity,view:next});
    }).catch(reason => {if (!controller.signal.aborted) setLoaded({key:identity,error:reason instanceof Error ? reason.message : 'Architecture unavailable'});});
    return () => controller.abort();
  },[projectId,revision,identity,attempt]);

  const graph = useMemo(() => {
    const visible = (view?.graph.nodes ?? []).filter(n => (!currentUseCase || n.use_case_ref === currentUseCase || !n.use_case_ref) && (references || (n.kind !== 'reference_report' && n.details.boundary !== 'excluded' && n.details.boundary !== 'fallback')));
    const ids = new Set(visible.map(n => n.id));
    const hasTransforms = visible.some(n => n.kind === 'transformation');
    const edges = (view?.graph.edges ?? []).filter(e => ids.has(e.source) && ids.has(e.target) && (lineage || !hasTransforms || e.kind !== 'declared_lineage'));
    const layout = new dagre.graphlib.Graph().setGraph({rankdir:'LR',nodesep:32,ranksep:96,marginx:24,marginy:24});
    layout.setDefaultEdgeLabel(() => ({}));
    visible.forEach(n => layout.setNode(n.id,{width:250,height:108}));
    edges.forEach(e => layout.setEdge(e.source,e.target));
    dagre.layout(layout);
    const nodes:CanvasNode[] = visible.map(n => {const p = layout.node(n.id);return {id:n.id,kind:kinds[n.kind] ?? 'derived',label:n.label,sub:[typeof n.details.type === 'string' ? n.details.type : undefined,n.layer,n.use_case_ref].filter(Boolean).join(' · '),description:Object.entries(n.details).filter(([,v]) => typeof v === 'string').map(([key,v]) => `${title(key)}: ${v}`).join('\n'),x:p.x-125,y:p.y-54,width:250,height:108};});
    return {nodes,edges:edges.map(e => ({source:e.source,target:e.target,relationship:e.label})) as CanvasEdge[]};
  },[view,currentUseCase,references,lineage]);

  async function generate(target:string) {
    const requested = identity; setBusyIdentity(identity); setMessage(null);
    try {
      const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/architecture`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revisionHash:revision,target,confirmGeneration:confirm})});
      if (!response.ok) {const data = await response.json();throw new Error(data.error?.message ?? 'Generation failed');}
      const blob = await response.blob();
      if (active.current !== requested) return;
      const url = URL.createObjectURL(blob);const a = document.createElement('a');a.href=url;a.download=`${projectId}-${target}-${revision?.slice(0,12)}.json`;a.click();URL.revokeObjectURL(url);
      setMessage({key:requested,text:'Generated files downloaded with their pinned revision and hashes. Nothing was applied to a tenant.'});
    } catch(reason) {if (active.current === requested) setMessage({key:requested,text:reason instanceof Error ? reason.message : 'Generation failed'});}
    finally {if(active.current === requested)setBusyIdentity(null);}
  }

  return <div className={styles.page}>
    <StudioPageHeader compact title="Architecture" description={`${projectName} · generated from the selected Project Package, without inferred tool defaults.`} actions={<StudioButton onClick={latest}>Load latest version</StudioButton>} />
    {!view ? <><StudioEmptyState title={error ? 'Architecture unavailable' : 'Loading project architecture'} description={error ?? 'Reading and validating the pinned project contracts.'} />{error && <><StudioButton onClick={() => {retry();setAttempt(n => n + 1);}}>Try again</StudioButton><Link href="/package">Review or import the Project Package</Link></>}</> : <>
      <div className={styles.toolbar}><StudioSegmentedControl aria-label="Architecture section" value={tab} onChange={setTab} options={[{value:'graph',label:'Architecture graph'},{value:'contracts',label:'Contracts & rationale'},{value:'outputs',label:'Build outputs'}]} /><span className={styles.note} title={revision ?? ''}>Version {revision?.slice(0,12)} · apply not enabled</span></div>
      {tab === 'graph' && <>
        <div className={styles.toolbar}><label>Use case <select aria-label="Architecture use case" value={currentUseCase} onChange={e => setUseCase(e.target.value)}><option value="">All recorded use cases</option>{view.use_cases.map(uc => <option key={String(uc.id)} value={String(uc.id)}>{String(uc.name ?? uc.id)}</option>)}</select></label><label><input type="checkbox" checked={references} onChange={e => setReferences(e.target.checked)} /> Reference reports and alternative/excluded sources</label><label><input type="checkbox" checked={lineage} onChange={e => setLineage(e.target.checked)} /> Additional lineage</label></div>
        <p className={styles.note}>Connectors distinguish declared data relationships, workspace ownership and build dependencies. Only explicit relationships are shown; reference reports remain separate from target reports.</p>
        {graph.nodes.length ? <div className={styles.canvas}><CustomCanvas nodes={graph.nodes} edges={graph.edges} /></div> : <StudioEmptyState title="No detailed architecture objects recorded" description="Add source, product and transformation contracts in use_case_delivery, or explicit physical_workspaces. Domain scope alone does not define an executable architecture." />}
        <details className={styles.details}><summary>Domain and environment scope</summary><ContractValue value={view.architecture} /></details>
      </>}
      {tab === 'contracts' && <>
        <p className={styles.note}>Review the source boundary, data products, transformation choices, semantic design and evidence gates. These are recorded contracts, not proof of deployed behavior.</p>
        {view.use_cases.map(uc => <details className={styles.details} key={String(uc.id)}><summary>{String(uc.name ?? uc.id)}</summary><ContractValue value={uc} /></details>)}
        {!view.use_cases.length && <StudioEmptyState title="No detailed use-case contracts recorded" description="Capture the design and rationale in the Project Package; this view will not substitute a library example." />}
      </>}
      {tab === 'outputs' && <>
        <StudioPanel title="Generation boundary" description="Review and attest the exact approved input version in Generate before requesting outputs. Generation does not approve or apply a tenant change."><Link href="/generate">Review input release</Link><p><Link href="/automation">Run coordinated generation, including native item definitions</Link></p><ul>{view.readiness.blockers.map(b => <li key={b}>{title(b)}</li>)}</ul></StudioPanel>
        <label className={styles.confirm}><input type="checkbox" checked={confirm} onChange={e => setConfirmedIdentity(e.target.checked ? identity : null)} /> Generate files from this released revision only. Do not deploy.</label>
        <div className={styles.outputs}>{view.outputs.map(output => <StudioPanel key={output.id} title={output.label} description={output.reason}><p>{output.status === 'ready' ? 'Generator supported for the recorded input; release checks still apply.' : 'Blocked by missing or unsupported input.'}</p><StudioButton disabled={busy || !confirm || output.status !== 'ready' || !view.readiness.release_ready} onClick={() => void generate(output.id)}>Generate {output.id === 'architecture_bundle' ? 'architecture bundle' : 'workspace requests'}</StudioButton></StudioPanel>)}</div>
        <p role="status">{notice}</p>
      </>}
    </>}
  </div>;
}
