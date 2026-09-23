'use client';

import { useState } from 'react';
import Link from 'next/link';
import { StudioButton, StudioEmptyState, StudioPageHeader, StudioPanel, StudioSegmentedControl } from '@/components/ui/studio-page';
import { usePinnedProject } from './use-pinned-project';
import styles from './delivery-workspace.module.css';
import { ProjectDeliveryAssurance } from './project-delivery-assurance';

type Item = Record<string, unknown>;
const object = (v: unknown): Item => v && typeof v === 'object' && !Array.isArray(v) ? v as Item : {};
const list = (v: unknown): Item[] => Array.isArray(v) ? v.map(object) : [];
const strings = (v: unknown): string[] => Array.isArray(v) ? v.map(String) : [];
const label = (v: unknown) => v === null || v === undefined || v === '' ? 'Not recorded' : String(v);
type Tab = 'scope' | 'plan' | 'decisions' | 'assurance';

export function DeliveryWorkspace() {
  const {projectName,revision,value,error,retry,latest} = usePinnedProject();
  const [tab,setTab] = useState<Tab>('plan');
  const read = (type: string) => value?.modules.find(m => m.type === type)?.data ?? {};
  const scope = read('opportunity'); const commercial = read('commercial'); const plan = read('plan');
  const work = list(plan.work_packages); const decisions = read('decision_set');
  const definitions = list(decisions.definitions); const instances = list(decisions.instances);
  const roles = [...new Set(work.flatMap(w => strings(w.role_refs)))];
  const milestones = list(plan.milestones); const tasks = list(plan.tasks);
  const staffing = object(plan.staffing); const assignments = list(staffing.assignments);
  const referenceLabels = object(plan.reference_labels);
  const readableRef = (ref: string) => label(referenceLabels[ref] ?? ref.replaceAll('_', ' '));
  const refs = (value: unknown) => strings(value).map(readableRef);
  return <div className={styles.page}>
    <StudioPageHeader compact title="Decide & plan" description={`${projectName} · turn scope and decisions into milestones, accountable work and verifiable completion.`} actions={<><Link href="/automation">Open build & release</Link><StudioButton onClick={latest}>Load latest version</StudioButton></>} />
    {!value ? <><StudioEmptyState title={error ? 'Project version unavailable' : 'Loading project version'} description={error ?? 'Reading the selected Project Package.'} />{error && <><StudioButton onClick={retry}>Try again</StudioButton><Link href="/package">Open Project Package</Link></>}</> : <>
      <div className={styles.context}><span>Saved version {value.revision.revision} · {value.state}</span><span title={revision ?? ''}>Fingerprint {revision?.slice(0,12)}</span><Link href="/package">Review or edit the source package</Link></div>
      <StudioSegmentedControl aria-label="Decide and plan section" value={tab} onChange={setTab} options={[{value:'plan',label:'Plan & roles'},{value:'decisions',label:'Decisions & workshops'},{value:'scope',label:'Scope & offer'},{value:'assurance',label:'Assurance'}]} />
      {tab === 'scope' && <div className={styles.grid}>
        <StudioPanel title="Scope and objectives"><p>Status: {label(scope.scope_status)}</p><ul>{strings(scope.objectives).map((s,i) => <li key={i}>{s}</li>)}</ul><h4>Constraints</h4>{strings(scope.constraints).length ? <ul>{strings(scope.constraints).map((s,i) => <li key={i}>{s}</li>)}</ul> : <p>No constraints recorded.</p>}</StudioPanel>
        <StudioPanel title="Commercial basis"><dl className={styles.facts}><dt>Status</dt><dd>{label(commercial.status)}</dd><dt>Estimate</dt><dd>{object(commercial.estimate).value == null ? 'Not estimated' : `${label(object(commercial.estimate).value)} ${label(commercial.currency)}`}</dd><dt>Authority</dt><dd>{label(commercial.authority_ref)}</dd><dt>Basis references</dt><dd>{strings(object(commercial.estimate).basis_refs).join(', ') || 'Not recorded'}</dd></dl><p className={styles.note}>An estimate is not an approved offer. Project-specific pricing stays with its commercial authority; no default rate or margin is inferred.</p></StudioPanel>
      </div>}
      {tab === 'plan' && <>
        <div className={styles.planMetrics}>
          <span><small>Milestones</small><strong>{milestones.filter(m => m.status === 'complete').length}/{milestones.length || '—'}</strong></span>
          <span><small>Open tasks</small><strong>{tasks.filter(t => t.status !== 'done').length}</strong></span>
          <span><small>Blocked</small><strong>{tasks.filter(t => t.status === 'blocked').length}</strong></span>
          <span><small>Staffed roles</small><strong>{assignments.filter(a => a.state === 'confirmed').length}/{assignments.length || '—'}</strong></span>
        </div>

        <StudioPanel title="Milestone path" description="Outcome gates and their explicit Definition of Done. Dates are shown only when they are recorded.">
          {milestones.length ? <ol className={styles.milestones}>{milestones.map((milestone,index) => <li key={String(milestone.id)} data-state={String(milestone.status)}>
            <div className={styles.milestoneMarker}><span>{String(index + 1).padStart(2,'0')}</span></div>
            <div className={styles.milestoneBody}><div className={styles.cardHead}><div><small>{label(milestone.target_gate)}</small><h3>{label(milestone.title)}</h3></div><span data-state={String(milestone.status)}>{label(milestone.status)}</span></div>
              <p>Accountable: {readableRef(String(milestone.owner_ref))}</p>
              <details className={styles.inlineDetails}><summary>Definition of Done · {strings(milestone.definition_of_done).length} checks</summary><ul className={styles.checklist}>{strings(milestone.definition_of_done).map((item,i) => <li key={i}>{item}</li>)}</ul></details>
            </div>
          </li>)}</ol> : <p>No milestones recorded.</p>}
        </StudioPanel>

        <StudioPanel title="Delivery tasks" description="The work queue connects ownership, decision dependencies and verifiable completion criteria.">
          {tasks.length ? <div className={styles.taskBoard}>{(['doing','blocked','ready','todo','done'] as const).map(state => {
            const stateTasks = tasks.filter(task => task.status === state); if (!stateTasks.length) return null;
            return <section key={state} className={styles.taskColumn} data-state={state}><header><span>{state.replace('_',' ')}</span><strong>{stateTasks.length}</strong></header>{stateTasks.map(task => <article key={String(task.id)} className={styles.taskCard}>
              <div className={styles.cardHead}><h3>{label(task.title)}</h3><span data-priority={String(task.priority)}>{label(task.priority)}</span></div>
              <p>{readableRef(String(task.owner_ref))} · {label(task.target_gate)}</p>
              {refs(task.decision_refs).length > 0 && <div className={styles.referenceList}>{refs(task.decision_refs).map((ref,i) => <span key={i}>{ref}</span>)}</div>}
              <details className={styles.inlineDetails}><summary>Definition of Done</summary><ul className={styles.checklist}>{strings(task.definition_of_done).map((item,i) => <li key={i}>{item}</li>)}</ul>{strings(task.evidence_refs).length > 0 && <p className={styles.evidence}>Evidence: {refs(task.evidence_refs).join(' · ')}</p>}</details>
            </article>)}</section>;
          })}</div> : <p>No delivery tasks recorded.</p>}
        </StudioPanel>

        <StudioPanel title="Staffing and accountability" description={staffing.delivery_model ? label(staffing.delivery_model) : 'No delivery model recorded.'}>
          {assignments.length ? <div className={styles.staffingGrid}>{assignments.map(assignment => <article key={String(assignment.id)} className={styles.staffCard}>
            <div className={styles.cardHead}><div><small>{readableRef(String(assignment.role_ref))}</small><h3>{readableRef(String(assignment.person_ref))}</h3></div><span data-state={String(assignment.state)}>{label(assignment.state)}</span></div>
            <p>{label(assignment.responsibility)}</p><dl><dt>Allocation</dt><dd>{assignment.allocation_percent == null ? 'Not committed' : `${label(assignment.allocation_percent)}%`}</dd><dt>Basis</dt><dd>{readableRef(String(assignment.basis_ref))}</dd></dl>
          </article>)}</div> : <p>No named staffing assignments recorded.</p>}
          <p className={styles.note}>A confirmed responsibility is not a capacity commitment. Allocation remains uncommitted unless a percentage and authority basis are recorded.</p>
        </StudioPanel>

        <details className={styles.details}><summary>Work packages, dependencies and effort basis</summary>
          <div className={styles.tableWrap}><table className={styles.table}><thead><tr><th scope="col">Work package</th><th scope="col">Status</th><th scope="col">Effort / basis</th><th scope="col">Required roles</th><th scope="col">Decision dependencies</th></tr></thead><tbody>{work.map(w => <tr key={String(w.id)}><td>{label(w.title)}</td><td>{label(w.status)}</td><td>{object(w.effort).value == null ? 'Not estimated' : `${label(object(w.effort).value)} ${label(object(w.effort).unit)}`} · {label(object(w.effort).provenance)}</td><td>{strings(w.role_refs).map(readableRef).join(', ') || 'Not recorded'}</td><td>{refs(w.decision_refs).join(', ') || 'None recorded'}</td></tr>)}</tbody></table></div>
          {!work.length && <p>No work packages recorded.</p>}
          <div className={styles.grid}><div><h3>Required roles</h3><ul>{roles.map(role => <li key={role}>{readableRef(role)}</li>)}</ul></div><div><h3>Dependencies</h3><ul>{list(plan.dependencies).map((d,i) => <li key={i}>{readableRef(String(d.predecessor_ref))} → {readableRef(String(d.successor_ref))}</li>)}</ul>{!list(plan.dependencies).length && <p>No predecessor relationships recorded.</p>}</div></div>
        </details>
      </>}
      {tab === 'decisions' && <>
        <p className={styles.note}>Use the recorded owner and due gate to prepare the relevant workshop. No meetings are scheduled by this view. Recommendations and approvals remain separate.</p>
        {definitions.map(definition => <details className={styles.details} key={String(definition.id)}><summary>{label(definition.title)} · {label(object(definition.due).gate)}</summary><dl className={styles.facts}><dt>Decision owner</dt><dd>{label(object(definition.decider).text)}</dd><dt>Question</dt><dd>{label(object(definition.question).technical_text)}</dd><dt>Recommendation</dt><dd>{label(object(definition.recommendation).text)}</dd><dt>If unresolved</dt><dd>{label(definition.consequence_if_unresolved)}</dd><dt>Recorded status</dt><dd>{instances.filter(i => i.definition_ref === definition.id).map(i => label(object(i.approval).state)).join(', ') || 'No outcome recorded'}</dd></dl><Link href="/approvals">Review options and evidence</Link></details>)}
        {!definitions.length && <StudioEmptyState title="No decisions recorded" description="Capture project questions and evidence before treating the design as agreed." />}
      </>}
      {tab === 'assurance' && revision && <ProjectDeliveryAssurance projectId={value.projectId} revision={revision} modules={value.modules} />}
    </>}
  </div>;
}
