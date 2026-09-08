'use client';

import { useState } from 'react';
import Link from 'next/link';
import { StudioButton, StudioEmptyState, StudioPageHeader, StudioPanel, StudioSegmentedControl } from '@/components/ui/studio-page';
import { usePinnedProject } from './use-pinned-project';
import styles from './delivery-workspace.module.css';

type Item = Record<string, unknown>;
const object = (v: unknown): Item => v && typeof v === 'object' && !Array.isArray(v) ? v as Item : {};
const list = (v: unknown): Item[] => Array.isArray(v) ? v.map(object) : [];
const strings = (v: unknown): string[] => Array.isArray(v) ? v.map(String) : [];
const label = (v: unknown) => v === null || v === undefined || v === '' ? 'Not recorded' : String(v);
type Tab = 'journey' | 'scope' | 'plan' | 'decisions';

export function DeliveryWorkspace() {
  const {projectName,revision,value,error,retry,latest} = usePinnedProject();
  const [tab,setTab] = useState<Tab>('journey');
  const read = (type: string) => value?.modules.find(m => m.type === type)?.data ?? {};
  const scope = read('opportunity'); const commercial = read('commercial'); const plan = read('plan');
  const work = list(plan.work_packages); const decisions = read('decision_set');
  const definitions = list(decisions.definitions); const instances = list(decisions.instances);
  const roles = [...new Set(work.flatMap(w => strings(w.role_refs)))];
  const stages = [
    {title:'Scope & offer',source:'opportunity + commercial',href:'/engagement',action:() => setTab('scope'),present:!!value?.modules.some(m => m.type === 'opportunity'),description:'Agree objectives, constraints, scope and the basis of the estimate. Commercial approval is recorded separately from delivery approval.'},
    {title:'Discovery',source:'saved project evidence',href:'/discover',description:'Collect sources and review extracted proposals. Transfer selected evidence to a working Package revision; suggestions never become approvals automatically.'},
    {title:'Decisions & plan',source:'decision_set + plan',href:'/engagement',action:() => setTab('decisions'),present:!!value?.modules.some(m => m.type === 'decision_set'),description:'Record options, consequences, required evidence and decision owners. Link work packages and required roles to the decisions they depend on.'},
    {title:'Architecture',source:'architecture_input + use_case_delivery',href:'/architecture',present:!!value?.modules.some(m => m.type === 'architecture_input' || m.type === 'use_case_delivery'),description:'Inspect the recorded topology, sources, products, transformations and serving contracts. Missing definitions are visible gaps, not generated assumptions.'},
    {title:'Build & release',source:'approved revision + generated outputs',href:'/generate',description:'Release exact inputs, inspect supported target outputs and resolve generation blockers. A generated file is not proof that deployment succeeded.'},
    {title:'Verify & operate',source:'observed_state + artifact_registry',href:'/health',present:!!value?.modules.some(m => m.type === 'observed_state'),description:'Compare implementation evidence with the approved design. Record acceptance and operating ownership; absent evidence stays unverified.'},
  ];
  return <div className={styles.page}>
    <StudioPageHeader compact title="Delivery workspace" description={`${projectName} · scope to verified delivery, using one versioned project model.`} actions={<><Link href="/automation">Open automation</Link><StudioButton onClick={latest}>Load latest version</StudioButton></>} />
    {!value ? <><StudioEmptyState title={error ? 'Project version unavailable' : 'Loading project version'} description={error ?? 'Reading the selected Project Package.'} />{error && <><StudioButton onClick={retry}>Try again</StudioButton><Link href="/package">Open Project Package</Link></>}</> : <>
      <div className={styles.context}><span>Saved version {value.revision.revision} · {value.state}</span><span title={revision ?? ''}>Fingerprint {revision?.slice(0,12)}</span><Link href="/package">Review or edit the source package</Link></div>
      <StudioSegmentedControl aria-label="Delivery workspace section" value={tab} onChange={setTab} options={[{value:'journey',label:'Delivery map'},{value:'scope',label:'Scope & offer'},{value:'plan',label:'Plan & roles'},{value:'decisions',label:'Decisions & workshops'}]} />
      {tab === 'journey' && <>
        <p className={styles.note}>This is one delivery workflow. Module presence below means content is recorded, not approved or implemented. Select a stage to work on it.</p>
        <ol className={styles.journey}>{stages.map((stage,index) => <li key={stage.title}><span className={styles.step}>{index + 1}</span><div><h2>{stage.title}</h2><p>{stage.description}</p><div className={styles.meta}><code>{stage.source}</code>{stage.present !== undefined && <span>{stage.present ? 'Module recorded' : 'Module not recorded'}</span>}</div>{stage.action ? <StudioButton onClick={stage.action}>Open {stage.title.toLowerCase()}</StudioButton> : <Link href={stage.href}>Open {stage.title.toLowerCase()}</Link>}</div></li>)}</ol>
        <details className={styles.details}><summary>Where each capability belongs</summary><div className={styles.tableWrap}><table className={styles.table}><thead><tr><th scope="col">Capability</th><th scope="col">Design and evidence</th><th scope="col">Delivery output</th></tr></thead><tbody>
          <tr><td>Data architecture & engineering</td><td>Architecture: domains, source contracts, products, transformations and environments.</td><td>Supported generated artifacts; explicit missing-input and adapter blockers.</td></tr>
          <tr><td>Semantic models & reporting</td><td>Use-case delivery: grains, relationships, security, model and report contracts.</td><td>Versioned design. Executable definitions require a supported, fully configured target adapter.</td></tr>
          <tr><td>Data governance</td><td>Decisions and contracts: ownership, access, quality, lineage and retention.</td><td>Policy and control specifications with observed evidence. Merely selecting a policy does not enforce it.</td></tr>
          <tr><td>CI/CD & operations</td><td>Environment, release, identity, recovery and acceptance contracts.</td><td>Gated outputs and readback evidence. Tenant apply is not executed from this view.</td></tr>
          <tr><td>Commercials & staffing</td><td>Scope, estimate basis and required role references in the plan.</td><td>Private cost and staffing scenarios in Automation. Rates and availability are explicit inputs; a scenario does not approve an offer or commit a person.</td></tr>
        </tbody></table></div></details>
      </>}
      {tab === 'scope' && <div className={styles.grid}>
        <StudioPanel title="Scope and objectives"><p>Status: {label(scope.scope_status)}</p><ul>{strings(scope.objectives).map((s,i) => <li key={i}>{s}</li>)}</ul><h4>Constraints</h4>{strings(scope.constraints).length ? <ul>{strings(scope.constraints).map((s,i) => <li key={i}>{s}</li>)}</ul> : <p>No constraints recorded.</p>}</StudioPanel>
        <StudioPanel title="Commercial basis"><dl className={styles.facts}><dt>Status</dt><dd>{label(commercial.status)}</dd><dt>Estimate</dt><dd>{object(commercial.estimate).value == null ? 'Not estimated' : `${label(object(commercial.estimate).value)} ${label(commercial.currency)}`}</dd><dt>Authority</dt><dd>{label(commercial.authority_ref)}</dd><dt>Basis references</dt><dd>{strings(object(commercial.estimate).basis_refs).join(', ') || 'Not recorded'}</dd></dl><p className={styles.note}>An estimate is not an approved offer. Project-specific pricing stays with its commercial authority; no default rate or margin is inferred.</p></StudioPanel>
      </div>}
      {tab === 'plan' && <>
        <StudioPanel title="Work packages" description="Recorded work, not an automatically optimized schedule."><div className={styles.tableWrap}><table className={styles.table}><thead><tr><th scope="col">Work package</th><th scope="col">Status</th><th scope="col">Effort / basis</th><th scope="col">Required roles</th><th scope="col">Decision dependencies</th></tr></thead><tbody>{work.map(w => <tr key={String(w.id)}><td>{label(w.title)}</td><td>{label(w.status)}</td><td>{object(w.effort).value == null ? 'Not estimated' : `${label(object(w.effort).value)} ${label(object(w.effort).unit)}`} · {label(object(w.effort).provenance)}</td><td>{strings(w.role_refs).join(', ') || 'Not recorded'}</td><td>{strings(w.decision_refs).join(', ') || 'None recorded'}</td></tr>)}</tbody></table></div>{!work.length && <p>No work packages recorded.</p>}</StudioPanel>
        <div className={styles.grid}><StudioPanel title="Required roles"><ul>{roles.map(role => <li key={role}>{role}</li>)}</ul><p className={styles.note}>These are role requirements, not named staffing assignments or availability commitments.</p></StudioPanel><StudioPanel title="Work dependencies"><ul>{list(plan.dependencies).map((d,i) => <li key={i}>{label(d.predecessor_ref)} → {label(d.successor_ref)}</li>)}</ul>{!list(plan.dependencies).length && <p>No predecessor relationships recorded.</p>}</StudioPanel></div>
      </>}
      {tab === 'decisions' && <>
        <p className={styles.note}>Use the recorded owner and due gate to prepare the relevant workshop. No meetings are scheduled by this view. Recommendations and approvals remain separate.</p>
        {definitions.map(definition => <details className={styles.details} key={String(definition.id)}><summary>{label(definition.title)} · {label(object(definition.due).gate)}</summary><dl className={styles.facts}><dt>Decision owner</dt><dd>{label(object(definition.decider).text)}</dd><dt>Question</dt><dd>{label(object(definition.question).technical_text)}</dd><dt>Recommendation</dt><dd>{label(object(definition.recommendation).text)}</dd><dt>If unresolved</dt><dd>{label(definition.consequence_if_unresolved)}</dd><dt>Recorded status</dt><dd>{instances.filter(i => i.definition_ref === definition.id).map(i => label(object(i.approval).state)).join(', ') || 'No outcome recorded'}</dd></dl><Link href="/approvals">Review options and evidence</Link></details>)}
        {!definitions.length && <StudioEmptyState title="No decisions recorded" description="Capture project questions and evidence before treating the design as agreed." />}
      </>}
    </>}
  </div>;
}
