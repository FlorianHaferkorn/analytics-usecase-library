'use client';

import { useEffect, useState } from 'react';
import { StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';
import type { DeliveryQualityAssessment } from '@/lib/bridge/project-assurance';
import type { ProjectProjection } from '@/lib/project-package/projection';
import styles from './delivery-workspace.module.css';

type Row = Record<string, unknown>;
const object = (value: unknown): Row => value && typeof value === 'object' && !Array.isArray(value) ? value as Row : {};
const rows = (value: unknown): Row[] => Array.isArray(value) ? value.map(object) : [];
const text = (value: unknown, fallback = 'Not recorded') => value === null || value === undefined || value === '' ? fallback : String(value);
const strings = (value: unknown): string[] => Array.isArray(value) ? value.map(String) : [];

export function ProjectDeliveryAssurance({ projectId, revision, modules }: { projectId: string; revision: string; modules: ProjectProjection['modules'] }) {
  const key = `${projectId}:${revision}`;
  const [loaded, setLoaded] = useState<{ key: string; assessment?: DeliveryQualityAssessment; error?: string } | null>(null);
  const result = loaded?.key === key ? loaded : null;
  useEffect(() => {
    const controller = new AbortController();
    void fetch(`/api/projects/${encodeURIComponent(projectId)}/assurance?revision=${revision}`, { cache: 'no-store', signal: controller.signal })
      .then(async response => {
        const body = await response.json();
        if (!response.ok) throw new Error(body.error?.message ?? `Assessment unavailable (${response.status})`);
        if (body.project_ref !== projectId) throw new Error('Assessment project mismatch');
        setLoaded({ key, assessment: body as DeliveryQualityAssessment });
      }).catch(error => { if (!controller.signal.aborted) setLoaded({ key, error: error instanceof Error ? error.message : 'Assessment unavailable' }); });
    return () => controller.abort();
  }, [projectId, revision, key]);

  const read = (type: string) => modules.find(module => module.type === type)?.data ?? {};
  const referenceLabels = object(read('plan').reference_labels);
  const readableRef = (value: unknown) => {
    const ref = text(value);
    if (referenceLabels[ref]) return text(referenceLabels[ref]);
    if (/^E-\d+$/.test(ref)) return `Recorded evidence (${ref})`;
    if (/^O-\d+$/.test(ref)) return `Open decision (${ref})`;
    if (/^K-\d+$/.test(ref)) return `Corrected project record (${ref})`;
    return ref.replaceAll('_', ' ');
  };
  const readableRefs = (value: unknown) => strings(value).map(readableRef);
  const identity = read('identity_access');
  const maintenance = read('architecture_maintenance');
  const decisions = read('decision_set');
  const definitions = new Map(rows(decisions.definitions).map(definition => [String(definition.id), definition]));

  return <div className={styles.assurance}>
    {!result ? <StudioEmptyState title="Assessing the pinned project version" description="Comparing recorded controls and evidence with the governed E2E delivery reference model." />
      : result.error ? <StudioEmptyState title="Delivery assessment unavailable" description={result.error} />
        : result.assessment && <>
          <StudioPanel title="Reference comparison" description={result.assessment.score_interpretation}>
            <div className={styles.scoreRow}><strong>{result.assessment.weighted_score}%</strong>{Object.entries(result.assessment.gates).map(([gate, state]) => <span key={gate} data-state={state.ready ? 'ready' : 'gap'}>{gate.replaceAll('_', ' ')} · {state.ready ? 'ready' : `${state.blockers.length} blocker${state.blockers.length === 1 ? '' : 's'}`}</span>)}</div>
            <p className={styles.note} data-state={result.assessment.reference_review.current ? 'ready' : 'gap'}>
              Expert-source review {result.assessment.reference_review.current ? 'current' : 'overdue'} · next due {new Date(result.assessment.reference_review.next_due_at).toLocaleDateString('en-GB')}
              {!result.assessment.reference_review.current && ` · ${result.assessment.reference_review.overdue_controls.length} affected control${result.assessment.reference_review.overdue_controls.length === 1 ? '' : 's'}`}
            </p>
            <div className={styles.tableWrap}><table className={styles.table}><thead><tr><th scope="col">Expert strength</th><th scope="col">Adopted control</th><th scope="col">Project evidence</th><th scope="col">Gate</th></tr></thead><tbody>{result.assessment.dimensions.flatMap(dimension => dimension.controls.map(control => <tr key={control.id}><td><a href={control.source.url} target="_blank" rel="noreferrer">{control.source.name}</a><br /><span className={styles.muted}>{control.source.strength_adopted}</span></td><td><strong>{control.title}</strong><br />{control.requirement}</td><td><span data-state={control.status}>{control.status}</span><br />{control.evidence}</td><td>{control.gate.replaceAll('_', ' ')}</td></tr>))}</tbody></table></div>
          </StudioPanel>
        </>}

    <div className={styles.grid}>
      <StudioPanel title="Required accounts and groups" description="Names are patterns. Credentials are never stored in the Project Package.">
        <div className={styles.tableWrap}><table className={styles.table}><thead><tr><th scope="col">Type</th><th scope="col">Identity</th><th scope="col">Purpose / owner</th><th scope="col">Environments</th><th scope="col">State</th></tr></thead><tbody>
          {rows(identity.accounts).map(item => <tr key={String(item.id)}><td>{text(item.principal_type)}</td><td><strong>{text(item.display_name_pattern)}</strong><br /><code>{text(item.id)}</code></td><td>{text(item.purpose)}<br />Owner: {readableRef(item.owner_ref)}</td><td>{strings(item.environments).join(', ')}</td><td>{text(item.lifecycle_state)}</td></tr>)}
          {rows(identity.groups).map(item => <tr key={String(item.id)}><td>{text(item.group_type)} group</td><td><strong>{text(item.display_name_pattern)}</strong><br /><code>{text(item.id)}</code></td><td>{text(item.purpose)}<br />Owners: {readableRefs(item.owner_refs).join(', ')}</td><td>{strings(item.environments).join(', ')}</td><td>{text(item.lifecycle_state)}</td></tr>)}
        </tbody></table></div>
        {!rows(identity.accounts).length && !rows(identity.groups).length && <p className={styles.note}>No identity and access module is recorded. Apply readiness remains unproven.</p>}
      </StudioPanel>
      <StudioPanel title="Role assignments and separation" description="Group-based human access, non-personal automation and independent production approval are explicit controls.">
        {rows(identity.role_assignments).map(item => <details className={styles.details} key={String(item.id)}><summary>{readableRef(item.subject_ref)} → {readableRef(item.role)} · {text(item.state)}</summary><dl className={styles.facts}><dt>Target</dt><dd>{readableRef(item.target_ref)}</dd><dt>Mode</dt><dd>{readableRef(item.assignment_mode)}</dd><dt>Approver</dt><dd>{readableRef(item.approver_ref)}</dd><dt>Evidence</dt><dd>{readableRefs(item.evidence_refs).join(', ') || 'Not recorded'}</dd></dl></details>)}
        {rows(identity.separation_rules).map(item => <details className={styles.details} key={String(item.id)}><summary>{readableRef(item.id)} · {text(item.state)}</summary><p>{text(item.scope)}</p><p>{readableRef(item.left_subject_ref)} ≠ {readableRef(item.right_subject_ref)}</p></details>)}
        {!rows(identity.role_assignments).length && <p className={styles.note}>No assignments are recorded.</p>}
      </StudioPanel>
    </div>

    <StudioPanel title="Architecture maintenance" description="The approved design remains linked to observed state, platform changes and evidence-backed retirement of transitional components.">
      {Object.keys(maintenance).length ? <>
        <dl className={styles.facts}>
          <dt>State</dt><dd>{text(maintenance.state)}</dd>
          <dt>Review owner</dt><dd>{readableRef(object(maintenance.review).owner_ref)}</dd>
          <dt>Review cycle</dt><dd>Every {text(object(maintenance.review).cadence_days)} days · last reviewed {text(object(maintenance.review).last_reviewed_at)}</dd>
          <dt>Drift policy</dt><dd>{text(object(maintenance.reconciliation).drift_action)} · unmanaged resources: {text(object(maintenance.reconciliation).unmanaged_resource_policy)}</dd>
          <dt>Reconciliation</dt><dd>{strings(object(maintenance.reconciliation).environments).join(', ') || 'Not recorded'} · {text(object(maintenance.reconciliation).last_result)} at {text(object(maintenance.reconciliation).last_reconciled_at)} · remediation SLA {text(object(maintenance.reconciliation).remediation_sla_hours)} hours</dd>
        </dl>
        <div className={styles.grid}>
          <div><h3>Technology watch</h3>{rows(maintenance.technology_watch).map(item => <details className={styles.details} key={String(item.id)}><summary>{text(item.name)} · {readableRef(item.change_policy)}</summary><p>{text(item.current_baseline)}</p><p>Owner: {readableRef(item.owner_ref)} · reviewed {text(item.reviewed_at)} · every {text(item.review_interval_days)} days</p><p><a href={text(item.authoritative_source)} target="_blank" rel="noreferrer">Authoritative source</a></p></details>)}</div>
          <div><h3>Architecture transitions</h3>{rows(maintenance.transitions).map(item => <details className={styles.details} key={String(item.id)}><summary>{readableRef(item.id)} · {text(item.state)}</summary><dl className={styles.facts}><dt>Current</dt><dd>{readableRef(item.current_ref)}</dd><dt>Target</dt><dd>{readableRef(item.target_ref)}</dd><dt>Owner</dt><dd>{readableRef(item.owner_ref)}</dd><dt>Rollback</dt><dd>{readableRef(item.rollback_ref)}</dd><dt>Retirement criteria</dt><dd>{strings(item.retirement_criteria).join(' · ')}</dd><dt>Evidence</dt><dd>{readableRefs(item.evidence_refs).join(', ') || 'Not recorded'}</dd></dl></details>)}</div>
        </div>
      </> : <p className={styles.note}>No architecture maintenance contract is recorded. Drift, platform changes and retirement remain unmanaged.</p>}
    </StudioPanel>

    <StudioPanel title="Architecture Decision Records" description="ADRs are rendered from the Decision Set. Recommendation, selection and human acceptance remain separate.">
      <div className={styles.tableWrap}><table className={styles.table}><thead><tr><th scope="col">ADR</th><th scope="col">Decision</th><th scope="col">Status</th><th scope="col">Decider / time</th><th scope="col">Evidence</th></tr></thead><tbody>{rows(decisions.instances).map(instance => {
        const definition = definitions.get(String(instance.definition_ref)) ?? {};
        const approval = object(instance.approval); const adr = object(definition.adr);
        return <tr key={String(instance.id)}><td>{text(adr.record_id, 'ADR metadata missing')}</td><td><strong>{text(definition.title)}</strong><br />{text(object(definition.question).technical_text)}</td><td>{text(approval.state)}</td><td>{text(approval.decided_by)}<br />{text(approval.decided_at)}</td><td>{readableRefs(approval.evidence_refs).join(', ') || 'Not recorded'}</td></tr>;
      })}</tbody></table></div>
      {!rows(decisions.instances).length && <p className={styles.note}>No project decisions are recorded. Build readiness remains unproven.</p>}
    </StudioPanel>
  </div>;
}
