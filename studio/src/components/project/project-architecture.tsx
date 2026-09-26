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
import { ProjectDecisionReview } from './project-decision-review';
import { useProjectStore } from '@/lib/store/project-store';
const title = (key:string) => key.replaceAll('_',' ').replace(/^./,s => s.toUpperCase());
function ContractValue({value}:{value:unknown}) {
  if (value == null || value === '') return <span className={styles.note}>Not recorded</span>;
  if (typeof value === 'boolean') return <span>{value ? 'Yes' : 'No'}</span>;
  if (Array.isArray(value)) return value.length ? <ul className={styles.values}>{value.map((v,i) => <li key={i}><ContractValue value={v} /></li>)}</ul> : <span className={styles.note}>None recorded</span>;
  if (typeof value === 'object') return <dl className={styles.facts}>{Object.entries(value).map(([key,v]) => <div key={key}><dt>{title(key)}</dt><dd>{typeof v === 'object' && v !== null ? <details><summary>Show {title(key).toLowerCase()}</summary><ContractValue value={v} /></details> : <ContractValue value={v} />}</dd></div>)}</dl>;
  return <span>{String(value)}</span>;
}
const kinds:Record<string,NodeKind> = {source:'source',data_product:'data_product',transformation:'transformation',reference_report:'reference_report',workspace:'workspace',domain:'domain',native_item:'native_item'};
type Tab = 'graph'|'contracts'|'decisions'|'outputs';
type DetailLevel = 'overview'|'full';

const STAGE_ORDER = ['platform', 'source', 'bronze', 'silver', 'gold', 'semantic', 'report', 'other'] as const;
const STAGE_LABELS: Record<string, string> = {
  platform: 'Platform', source: 'Sources', bronze: 'Bronze', silver: 'Silver',
  gold: 'Gold', semantic: 'Semantic model', report: 'Reports', other: 'Other',
};

function architectureStage(node: ArchitectureView['graph']['nodes'][number]) {
  if (node.layer && STAGE_ORDER.includes(node.layer as typeof STAGE_ORDER[number])) return node.layer;
  if (node.kind === 'source') return 'source';
  if (node.kind === 'reference_report') return 'report';
  if (node.kind === 'workspace' || node.kind === 'domain' || node.kind === 'native_item') return 'platform';
  return 'other';
}

export function ProjectArchitecture() {
  const {projectId,projectName,revision,error:packageError,latest,retry} = usePinnedProject();
  const [loaded,setLoaded] = useState<{key:string;view?:ArchitectureView;error?:string}|null>(null);
  const [attempt,setAttempt] = useState(0);
  const [tab,setTab] = useState<Tab>('graph');
  const [useCase,setUseCase] = useState('');
  const [references,setReferences] = useState(false);
  const [lineage,setLineage] = useState(false);
  const [detailLevel,setDetailLevel] = useState<DetailLevel>('overview');
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
  const soleUseCase = view?.use_cases.length === 1 ? String(view.use_cases[0].id ?? '') : '';
  const currentUseCase = view?.use_cases.some(uc => uc.id === useCase) ? useCase : soleUseCase;
  const error = packageError ?? (loaded?.key === identity ? loaded.error : undefined);
  const visibleElementCount = useMemo(() => (view?.graph.nodes ?? []).filter(node => (
    (!currentUseCase || node.use_case_ref === currentUseCase || !node.use_case_ref)
    && (references || (node.kind !== 'reference_report' && node.details.boundary !== 'excluded' && node.details.boundary !== 'fallback'))
  )).length, [view, currentUseCase, references]);
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
    if (detailLevel === 'overview') {
      const stageByNode = new Map(visible.map(node => [node.id, architectureStage(node)]));
      const stages = new Map<string, typeof visible>();
      visible.forEach(node => {
        const stage = stageByNode.get(node.id) ?? 'other';
        stages.set(stage, [...(stages.get(stage) ?? []), node]);
      });
      const overviewEdges = new Map<string, CanvasEdge>();
      edges.forEach(edge => {
        const sourceStage = stageByNode.get(edge.source);
        const targetStage = stageByNode.get(edge.target);
        if (!sourceStage || !targetStage || sourceStage === targetStage) return;
        const key = `${sourceStage}:${targetStage}`;
        overviewEdges.set(key, { source: `stage:${sourceStage}`, target: `stage:${targetStage}` });
      });
      const orderedStages = STAGE_ORDER.filter(stage => stages.has(stage));
      const layout = new dagre.graphlib.Graph().setGraph({rankdir:'LR',nodesep:16,ranksep:18,marginx:16,marginy:16});
      layout.setDefaultEdgeLabel(() => ({}));
      orderedStages.forEach(stage => layout.setNode(`stage:${stage}`, {width:140,height:80}));
      [...overviewEdges.values()].forEach(edge => layout.setEdge(edge.source, edge.target));
      dagre.layout(layout);
      const nodes: CanvasNode[] = orderedStages.map(stage => {
        const members = stages.get(stage) ?? [];
        const position = layout.node(`stage:${stage}`);
        const examples = members.slice(0, 6).map(node => node.label);
        return {
          id: `stage:${stage}`,
          kind: stage === 'source' ? 'source' : 'data_product',
          label: STAGE_LABELS[stage] ?? title(stage),
          sub: `${members.length} ${members.length === 1 ? 'element' : 'elements'}`,
          description: `${examples.join('\n')}${members.length > examples.length ? `\n+ ${members.length - examples.length} more` : ''}`,
          x: position.x - 70,
          y: position.y - 40,
          width: 140,
          height: 80,
        };
      });
      return {nodes, edges: [...overviewEdges.values()]};
    }
    const orderedVisible = [...visible].sort((left, right) => {
      const stageDelta = STAGE_ORDER.indexOf(architectureStage(left) as typeof STAGE_ORDER[number]) - STAGE_ORDER.indexOf(architectureStage(right) as typeof STAGE_ORDER[number]);
      return stageDelta || left.label.localeCompare(right.label);
    });
    const layout = new dagre.graphlib.Graph().setGraph({rankdir:'LR',nodesep:24,ranksep:72,marginx:24,marginy:24});
    layout.setDefaultEdgeLabel(() => ({}));
    orderedVisible.forEach(n => layout.setNode(n.id,{width:224,height:92}));
    edges.forEach(e => layout.setEdge(e.source,e.target));
    dagre.layout(layout);
    const nodes:CanvasNode[] = orderedVisible.map(n => {const p = layout.node(n.id);return {id:n.id,kind:kinds[n.kind] ?? 'derived',label:n.label,sub:[typeof n.details.type === 'string' ? n.details.type : undefined,n.layer,n.use_case_ref].filter(Boolean).join(' · '),description:Object.entries(n.details).filter(([,v]) => typeof v === 'string').map(([key,v]) => `${title(key)}: ${v}`).join('\n'),x:p.x-112,y:p.y-46,width:224,height:92};});
    return {nodes,edges:edges.map(e => ({source:e.source,target:e.target,relationship:e.label})) as CanvasEdge[]};
  },[view,currentUseCase,references,lineage,detailLevel]);

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
      <div className={styles.toolbar}><StudioSegmentedControl aria-label="Architecture section" value={tab} onChange={setTab} options={[{value:'graph',label:'Architecture graph'},{value:'contracts',label:'Contracts & rationale'},{value:'decisions',label:'Decision effects'},{value:'outputs',label:'Build outputs'}]} /><span className={styles.note} title={revision ?? ''}>Version {revision?.slice(0,12)} · tenant apply not enabled</span></div>
      {notice && tab !== 'outputs' && <p role="status" className={styles.note}>{notice}</p>}
      {tab === 'decisions' && revision && <ProjectDecisionReview key={identity} projectId={projectId} revisionHash={revision} onApplied={result => {
        const selected = useProjectStore.getState();
        if (active.current !== identity || selected.projectId !== projectId || selected.packageRevisionHash !== revision) return;
        setMessage({key:`${projectId}:${result.revision_hash}`,text:'Architecture updated in a new Working version. Review the updated graph and contracts, then approve and release the new input version. Nothing was deployed.'});
        useProjectStore.getState().setPackageRevisionHash(result.revision_hash);
        setConfirmedIdentity(null); setTab('graph');
      }} />}
      {tab === 'graph' && <>
        <div className={styles.toolbar}>
          <StudioSegmentedControl aria-label="Architecture detail" value={detailLevel} onChange={setDetailLevel} options={[{value:'overview',label:'Flow overview'},{value:'full',label:`All elements · ${visibleElementCount}`}]} />
          <label>Use case <select aria-label="Architecture use case" value={currentUseCase} onChange={e => setUseCase(e.target.value)}><option value="">All recorded use cases</option>{view.use_cases.map(uc => <option key={String(uc.id)} value={String(uc.id)}>{String(uc.title ?? uc.name ?? uc.id)}</option>)}</select></label>
          <label><input type="checkbox" checked={references} onChange={e => setReferences(e.target.checked)} /> Reference and alternative sources</label>
          <label><input type="checkbox" checked={lineage} onChange={e => setLineage(e.target.checked)} /> Additional lineage</label>
        </div>
        <p className={styles.note}>{detailLevel === 'overview' ? 'Start with the governed end-to-end path. Select a stage to see representative contents; switch to all elements for the complete contract inventory.' : 'The complete contract inventory opens as a searchable list. Switch to Graph when spatial lineage is required.'}</p>
        {graph.nodes.length ? <div className={`${styles.canvas} ${detailLevel === 'overview' ? styles.overviewCanvas : ''}`}><CustomCanvas key={detailLevel} nodes={graph.nodes} edges={graph.edges} initialMode={detailLevel === 'overview' ? 'graph' : 'list'} hint={detailLevel === 'overview' ? 'Select a stage to focus the path and inspect representative contents.' : 'Search or select an element; Graph remains available for full lineage.'} /></div> : <StudioEmptyState title="No detailed architecture objects recorded" description="Add source, product and transformation contracts in use_case_delivery, or explicit physical_workspaces. Domain scope alone does not define an executable architecture." />}
        <details className={styles.details}><summary>Domain and environment scope</summary><ContractValue value={view.architecture} /></details>
      </>}
      {tab === 'contracts' && <>
        <p className={styles.note}>Review the source boundary, data products, transformation choices, semantic design and evidence gates. These are recorded contracts, not proof of deployed behavior.</p>
        {view.use_cases.map(uc => <details className={styles.details} key={String(uc.id)}><summary>{String(uc.title ?? uc.name ?? title(String(uc.id)))}</summary><ContractValue value={uc} /></details>)}
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
