'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useProjectStore } from '@/lib/store/project-store';
import { StudioButton, StudioEmptyState, StudioPageHeader, StudioPanel } from '@/components/ui/studio-page';
import type { ProjectProjection } from '@/lib/project-package/projection';
import { projectSurface } from '@/lib/project-package/view-policy';
import styles from './project-scope.module.css';
import { CustomCanvas } from '@/components/canvas/custom-canvas';
import type { CanvasNode, CanvasEdge } from '@/components/canvas/canvas-types';
import { DeliveryModel3D, type DeliveryStage } from './delivery-model-3d';

type Row = Record<string, unknown>;
function obj(value: unknown): Row { return value && typeof value === 'object' && !Array.isArray(value) ? value as Row : {}; }
function rows(value: unknown): Row[] { return Array.isArray(value) ? value.map(obj) : []; }
function text(value: unknown, fallback = 'Not recorded'): string {
  return value === null || value === undefined || value === '' ? fallback : typeof value === 'string' ? value : JSON.stringify(value);
}
function Detail({ title, value }: { title: string; value: unknown }) {
  return <details className={styles.details}><summary>{title}</summary><pre className={styles.raw}>{JSON.stringify(value, null, 2)}</pre></details>;
}

export function ProjectRevisionView({ pathname }: { pathname: string }) {
  const projectId = useProjectStore(s => s.projectId);
  const projectName = useProjectStore(s => s.projectName);
  const hash = useProjectStore(s => s.packageRevisionHash);
  const setHash = useProjectStore(s => s.setPackageRevisionHash);
  const [loaded, setLoaded] = useState<{ key: string; value: ProjectProjection } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const key = `${projectId}:${hash ?? 'HEAD'}`;
  const value = loaded?.key === key ? loaded.value : null;

  useEffect(() => {
    const abort = new AbortController();
    fetch(`/api/projects/${encodeURIComponent(projectId)}/view${hash ? `?revision=${hash}` : ''}`, { signal: abort.signal, cache: 'no-store' })
      .then(async response => {
        const body = await response.json();
        if (!response.ok) throw new Error(body.error?.message ?? `Project data unavailable (${response.status})`);
        const projection = body as ProjectProjection;
        if (projection.projectId !== projectId || (hash && projection.revision.revision_hash !== hash)) throw new Error('Project or revision mismatch');
        if (abort.signal.aborted || useProjectStore.getState().projectId !== projectId) return;
        const pinned = projection.revision.revision_hash;
        setError(null);
        setLoaded({ key: `${projectId}:${pinned}`, value: projection });
        setHash(pinned);
      }).catch(reason => { if (!abort.signal.aborted) { setLoaded(null); setError(reason instanceof Error ? reason.message : 'Unable to load project'); } });
    return () => abort.abort();
  }, [projectId, hash, setHash, retry]);

  if (!value) return <div className={styles.page}>
    <StudioPageHeader compact title={projectName} description="Project Package is the source for this view. Library content is never substituted." />
    {error ? <><StudioEmptyState title="Project version unavailable" description={error} /><StudioButton onClick={() => { setError(null); setRetry(n => n + 1); }}>Try again</StudioButton><Link href="/package">Open Project Package to import or review a version</Link></> : <p role="status">Loading project version…</p>}
  </div>;

  const getModule = (type: string) => value.modules.find(m => m.type === type)?.data ?? {};
  const plan = getModule('plan');
  const work = rows(plan.work_packages);
  const decisions = getModule('decision_set');
  const definitions = rows(decisions.definitions);
  const instances = rows(decisions.instances);
  const unresolved = instances.filter(item => ['draft', 'proposed', 'rejected', 'deferred'].includes(String(obj(item.approval).state)));
  const architecture = getModule('architecture_input');
  const opportunity = getModule('opportunity');
  const tasks = rows(plan.tasks);
  const milestones = rows(plan.milestones);
  const hasModule = (type: string) => value.modules.some(module => module.type === type);
  const hasObservedEvidence = value.modules.some(module => module.type === 'observed_state');
  const blockedTasks = tasks.filter(task => task.status === 'blocked');
  const activeTasks = tasks.filter(task => ['doing', 'ready'].includes(String(task.status)));
  const deliveryStages: DeliveryStage[] = [
    { step: '01', title: 'Discover', outcome: 'Scope and evidence', href: '/discover', state: hasModule('opportunity') ? 'recorded' : 'not_recorded', definition: hasModule('opportunity'), delivery: hasModule('artifact_registry'), evidence: hasModule('artifact_registry') },
    { step: '02', title: 'Decide & plan', outcome: 'Choices, plan and staffing', href: '/engagement', state: unresolved.length ? 'blocked' : hasModule('decision_set') && hasModule('plan') ? 'active' : 'not_recorded', definition: hasModule('decision_set'), delivery: hasModule('plan'), evidence: milestones.length > 0 },
    { step: '03', title: 'Design', outcome: 'Architecture and contracts', href: '/architecture', state: hasModule('architecture_input') ? 'recorded' : 'not_recorded', definition: hasModule('architecture_input'), delivery: hasModule('use_case_delivery'), evidence: hasModule('architecture_maintenance') },
    { step: '04', title: 'Build & release', outcome: 'Gated implementation', href: '/automation', state: blockedTasks.length ? 'blocked' : activeTasks.length ? 'active' : work.length > 0 && work.every(item => item.status === 'complete') ? 'complete' : 'recorded', definition: work.length > 0, delivery: work.some(item => ['active', 'complete'].includes(String(item.status))), evidence: hasObservedEvidence },
    { step: '05', title: 'Verify & operate', outcome: 'Acceptance and assurance', href: '/health', state: hasObservedEvidence ? 'active' : 'not_recorded', definition: hasModule('delivery_quality'), delivery: hasObservedEvidence, evidence: hasModule('artifact_registry') },
  ];
  const scopeNodes: CanvasNode[] = [];
  const scopeEdges: CanvasEdge[] = [];
  let scopeRow = 0;
  for (const domain of rows(architecture.domains)) {
    const domainId = `domain:${String(domain.id)}`;
    scopeNodes.push({id:domainId,kind:'domain',label:text(domain.id),sub:`Capacity: ${text(domain.capacity)}`,description:`Domain scope: ${text(domain.delivery_scope)}`,x:0,y:scopeRow * 140,width:260,height:108});
    const uses = rows(architecture.use_cases).filter(uc => uc.domain_ref === domain.id);
    uses.forEach((uc, index) => {
      const id = `usecase:${String(uc.id)}`;
      scopeNodes.push({id,kind:'bracket',label:text(uc.name),sub:text(uc.id),description:`Architecture detail: ${text(uc.architecture_detail)}`,x:380,y:(scopeRow + index)*140,width:260,height:108});
      scopeEdges.push({source:domainId,target:id,relationship:'Owns use case'});
    });
    scopeRow += Math.max(uses.length,1);
  }
  const mode = projectSurface(pathname);
  const titles = { overview: 'Delivery cockpit', architecture: 'Project architecture', decisions: 'Project decisions', assurance: 'Project evidence', unsupported: 'Project view not available' };
  return <div className={styles.page}>
    <StudioPageHeader compact title={titles[mode]} description={`${projectName} · Saved version ${value.revision.revision} · ${text(value.state)}. Changes and approvals are managed in Project Package.`}
      actions={<StudioButton onClick={() => { setLoaded(null); setHash(null); setRetry(n => n + 1); }}>Load latest version</StudioButton>} />
    <div className={styles.summary}><span>Version fingerprint<strong title={hash ?? ''}>{hash?.slice(0, 12)}</strong></span><span>Unresolved decisions<strong>{unresolved.length}</strong></span><span>Work completed<strong>{work.filter(w => w.status === 'complete').length} / {work.length}</strong></span></div>

    {mode === 'overview' && <>
      <DeliveryModel3D stages={deliveryStages} />
      <div className={styles.cockpitGrid}>
        <StudioPanel title="Next accountable action" description={blockedTasks.length ? `${blockedTasks.length} blocked task${blockedTasks.length === 1 ? '' : 's'} require resolution.` : unresolved.length ? `${unresolved.length} decision${unresolved.length === 1 ? '' : 's'} require resolution.` : 'Continue the next active delivery task.'}>
          {blockedTasks.length ? <><h3>{text(blockedTasks[0].title)}</h3><p>{text(blockedTasks[0].target_gate)}</p><Link href="/engagement">Open plan and Definition of Done</Link></> : unresolved.length ? <Link href="/approvals">Review project decisions</Link> : <Link href="/automation">Review build and release readiness</Link>}
        </StudioPanel>
        <StudioPanel title="Project control" description="Current package content; no approval or tenant state is inferred.">
          <dl className={styles.controlFacts}><dt>Milestones</dt><dd>{milestones.filter(item => item.status === 'complete').length} / {milestones.length || 'not recorded'} complete</dd><dt>Tasks</dt><dd>{tasks.filter(item => item.status === 'done').length} / {tasks.length || 'not recorded'} done</dd><dt>Work packages</dt><dd>{work.filter(item => item.status === 'complete').length} / {work.length} complete</dd></dl>
        </StudioPanel>
        <StudioPanel title="Scope outcome" description={`Scope status: ${text(opportunity.scope_status)}`}>
          <ul className={styles.compactList}>{(Array.isArray(opportunity.objectives) ? opportunity.objectives : []).slice(0, 3).map((item, i) => <li key={i}>{String(item)}</li>)}</ul>
          <Link href="/engagement">Review scope, decisions and staffing</Link>
        </StudioPanel>
      </div>
    </>}

    {mode === 'architecture' && <>
      <div className={styles.scope}>This is the recorded domain scope. <Link href="/architecture">Open detailed Architecture, contracts and build outputs</Link></div>
      <StudioPanel title="Architecture scope" description="Recorded package architecture, not the global KPI showcase. This module defines domains, use cases and contracts; it does not contain a complete physical artifact graph.">
        <p>{text(architecture.tenant)} · {text(architecture.region)} · {text(architecture.stack)}</p>
        {scopeNodes.length > 0 && <><p>Domain ownership → use case. These connectors represent scope, not physical data movement.</p><div className={styles.graph}><CustomCanvas nodes={scopeNodes} edges={scopeEdges} /></div></>}
        <div className={styles.grid}>{rows(architecture.domains).map((domain, i) => <StudioPanel key={i} title={text(domain.id)} description={`Capacity: ${text(domain.capacity)} · ${text(domain.delivery_scope)}`}>
          <ul>{rows(architecture.use_cases).filter(uc => uc.domain_ref === domain.id).map((uc, j) => <li key={j}>{text(uc.name)} · {text(uc.architecture_detail)}</li>)}</ul>
        </StudioPanel>)}</div>
        {!Object.keys(architecture).length && <p>No architecture module recorded in this version.</p>}
        <Detail title="Environments and decision reference" value={architecture.environments ?? { status: 'not_recorded' }} />
        <Detail title="Source and delivery contracts" value={architecture.contracts ?? []} />
        <Detail title="Artifact registry and provenance" value={getModule('artifact_registry')} />
      </StudioPanel>
    </>}

    {mode === 'decisions' && <StudioPanel title="Decisions, recommendations and evidence" description="Recorded approval is distinct from a recommendation. No decision is approved by opening this page.">
      {definitions.map((definition, i) => {
        const related = instances.filter(instance => instance.definition_ref === definition.id);
        return <details className={styles.details} key={i}><summary>{text(definition.title)} · {related.length ? related.map(r => text(obj(r.approval).state)).join(', ') : 'No instance recorded'}</summary>
          <dl><dt>Question</dt><dd>{text(obj(definition.question).technical_text)}</dd><dt>Recommendation</dt><dd>{text(obj(definition.recommendation).text)}</dd><dt>If unresolved</dt><dd>{text(definition.consequence_if_unresolved)}</dd><dt>Decision owner</dt><dd>{text(obj(definition.decider).text)}</dd></dl>
          {rows(definition.option_details).map((option, j) => <div key={j}><h3>{text(option.text)}</h3><p>Implication: {text(option.implication)}</p><Detail title="Advantages, limitations and sources" value={option} /></div>)}
          <Detail title="Recorded outcome and evidence" value={related} />
        </details>;
      })}
      {!definitions.length && <p>No decision definitions recorded.</p>}
    </StudioPanel>}

    {mode === 'assurance' && <StudioPanel title="Recorded evidence" description="These are observed-state records, not a new live validation run. Version approval does not certify a deployment.">{value.modules.filter(m => m.type === 'observed_state').map(m => <Detail key={m.path} title={`Environment: ${m.environment ?? 'Unspecified'}`} value={m.data} />)}<Detail title="Artifact lifecycle and publication evidence" value={getModule('artifact_registry')} /></StudioPanel>}
    {mode === 'unsupported' && <StudioEmptyState title="No project-specific implementation for this tool" description="Use Library mode to explore reusable examples. Those results are not project evidence. Open Project Package for the authoritative project content." />}
    <details className={styles.details}><summary>Version modules and source details</summary>{value.modules.map(m => <Detail key={m.path} title={`${text(m.type)} · ${m.path}`} value={m.data} />)}</details>
  </div>;
}
