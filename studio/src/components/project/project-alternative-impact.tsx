'use client';

import { useEffect, useState } from 'react';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';
import type { AlternativeImpact } from '@/lib/bridge/project-alternatives';
import { ProjectCommercialImpact } from './project-commercial-impact';
import { ProjectRunCostDelta } from './project-run-cost-delta';
import styles from './project-alternative-impact.module.css';

export interface AlternativeOption { decision_ref: string; option_ref: string; rule_id: string }

const label = (value: string) => value.replaceAll('_', ' ');
const effort = (totals: Record<string, number>) => Object.entries(totals).map(([unit, value]) => `${value} ${unit.replaceAll('_', '-')}`).join(' · ') || 'None';

function part(path: string) {
  const match = /^fabric\/(workspaces|items)\/([^/]+?)\.(?:request|definition)\.json$/.exec(path);
  return match ? { kind: match[1] === 'workspaces' ? 'Workspace' : 'Native item', id: match[2] } : { kind: 'File', id: path };
}

/** Read-only side-by-side of a declared alternative against the released baseline. */
export function ProjectAlternativeImpact({ projectId, revisionHash, options }: {
  projectId: string; revisionHash: string; options: AlternativeOption[];
}) {
  const [selected, setSelected] = useState<AlternativeOption | null>(null);
  const [impact, setImpact] = useState<AlternativeImpact | null>(null);
  const [error, setError] = useState('');
  const unique = options.filter((option, index) => options.findIndex(other => other.decision_ref === option.decision_ref && other.option_ref === option.option_ref) === index);

  useEffect(() => {
    if (!selected) return;
    const abort = new AbortController();
    const query = new URLSearchParams({ revision: revisionHash, decision: selected.decision_ref, option: selected.option_ref });
    void fetch(`/api/projects/${encodeURIComponent(projectId)}/architecture/alternatives?${query}`, { cache: 'no-store', signal: abort.signal })
      .then(async response => {
        const value = await response.json();
        if (!response.ok) throw new Error(typeof value.error === 'string' ? value.error : 'Alternative comparison unavailable');
        if (value.project_ref !== projectId || value.baseline_revision_hash !== revisionHash || value.alternative_option_ref !== selected.option_ref || value.baseline_unchanged !== true) {
          throw new Error('Alternative comparison project, revision or option mismatch');
        }
        if (!abort.signal.aborted) setImpact(value as AlternativeImpact);
      }).catch(reason => { if (!abort.signal.aborted) setError(reason instanceof Error ? reason.message : 'Alternative comparison unavailable'); });
    return () => abort.abort();
  }, [projectId, revisionHash, selected]);

  if (!unique.length) {
    return <StudioEmptyState title="No alternative mapped" description="Only options with an authored decision rule can be compared. Add a rule for the alternative option in architecture_input.decision_rules." />;
  }

  const view = impact && selected && impact.alternative_option_ref === selected.option_ref ? impact : null;
  const parts = view ? [
    ...view.impacts.manifests.removed.map(path => ({ ...part(path), change: 'Removed' })),
    ...view.impacts.manifests.added.map(path => ({ ...part(path), change: 'Added' })),
    ...view.impacts.manifests.changed.map(path => ({ ...part(path), change: 'Changed' })),
  ] : [];
  const execution = view?.impacts.tests.execution_obligations;

  return <section aria-label="Compare an alternative" className={styles.stack}>
    <div className={styles.picker} role="group" aria-label="Alternative options">
      {unique.map(option => <StudioButton key={`${option.decision_ref}:${option.option_ref}`}
        variant={selected?.decision_ref === option.decision_ref && selected.option_ref === option.option_ref ? 'primary' : 'secondary'}
        aria-pressed={selected?.decision_ref === option.decision_ref && selected.option_ref === option.option_ref}
        onClick={() => { setImpact(null); setError(''); setSelected(option); }}>{`${label(option.decision_ref)} → ${label(option.option_ref)}`}</StudioButton>)}
    </div>
    {!selected && <p className={styles.note}>Select an alternative to see what it would change. The released baseline stays as it is; nothing is approved, released or deployed.</p>}
    {selected && !view && <StudioEmptyState title={error ? 'Comparison unavailable' : 'Comparing with the released baseline'} description={error || 'Evaluating the recorded rules for this option against this exact version.'} />}
    {view && <>
      <p role="status" className={styles.note}>Hypothetical: {label(view.baseline_option_ref)} (released) compared with {label(view.alternative_option_ref)}. The baseline revision and its release record are unchanged. Roles and effort are package assumptions, not named staffing or cost.</p>
      {view.blockers.length > 0 && <StudioPanel title="This alternative is blocked"><ul className={styles.list}>{view.blockers.map((blocker, index) => <li key={`${index}:${blocker}`}>{blocker}</li>)}</ul></StudioPanel>}
      <dl className={styles.tiles} aria-label="Impact summary">
        <div><dt>Stages</dt><dd>{[...view.impacts.architecture.environments.removed.map(stage => `− ${stage.toUpperCase()}`), ...view.impacts.architecture.environments.added.map(stage => `+ ${stage.toUpperCase()}`)].join(' ') || 'Unchanged'}</dd></div>
        <div><dt>Role demand</dt><dd>{[...view.impacts.staffing.role_demand.removed.map(role => `− ${label(role)}`), ...view.impacts.staffing.role_demand.added.map(role => `+ ${label(role)}`)].join(' ') || 'Unchanged'}</dd></div>
        <div><dt>Effort</dt><dd>{effort(view.impacts.staffing.effort_totals.before)} → {effort(view.impacts.staffing.effort_totals.after)}</dd></div>
        <div><dt>Parts</dt><dd>{`−${view.impacts.manifests.removed.length} · +${view.impacts.manifests.added.length}`}</dd></div>
        <div><dt>Test obligations</dt><dd>{`−${execution?.removed.length ?? 0} · +${execution?.added.length ?? 0}`}</dd></div>
      </dl>
      {parts.length > 0 && <table className={styles.parts}>
        <caption>Parts list · workspaces and native items that change</caption>
        <thead><tr><th scope="col">Change</th><th scope="col">Kind</th><th scope="col">Identifier</th></tr></thead>
        <tbody>{parts.map(row => <tr key={`${row.change}:${row.kind}:${row.id}`}><td>{row.change}</td><td>{row.kind}</td><td className={styles.mono}>{row.id}</td></tr>)}</tbody>
      </table>}
      {(Object.keys(view.impacts.plan.work_packages).length > 0 || Object.keys(view.impacts.plan.tasks).length > 0) && <StudioPanel title="Delivery plan">
        <ul className={styles.list}>
          {Object.entries(view.impacts.plan.work_packages).map(([id, change]) => <li key={`wp:${id}`}><strong>{label(id)}</strong><span>{`${change.before?.role_refs.map(label).join(', ') ?? 'None'} · ${change.before?.effort.value ?? '?'} → ${change.after?.role_refs.map(label).join(', ') ?? 'None'} · ${change.after?.effort.value ?? '?'} ${change.after?.effort.unit.replaceAll('_', '-') ?? ''}`}</span></li>)}
          {Object.entries(view.impacts.plan.tasks).map(([id, change]) => <li key={`task:${id}`}><strong>{label(id)}</strong><span>{`${change.before?.join('; ') ?? 'None'} → ${change.after?.join('; ') ?? 'None'}`}</span></li>)}
        </ul>
      </StudioPanel>}
      {execution && (execution.added.length > 0 || execution.removed.length > 0) && <details className={styles.details}>
        <summary>Test obligations · {execution.removed.length} removed, {execution.added.length} added</summary>
        <ul className={styles.list}>
          {execution.removed.map(item => <li key={`r:${item}`} className={styles.mono}>− {item}</li>)}
          {execution.added.map(item => <li key={`a:${item}`} className={styles.mono}>+ {item}</li>)}
        </ul>
      </details>}
      <StudioPanel title="Before this alternative could be released">
        <ol className={styles.list}>{view.obligations.map(item => <li key={item.id}><strong>{label(item.id.split(':')[0])}{item.id.includes(':') ? ` · ${item.id.split(':').slice(1).join(':')}` : ''}</strong><span>{item.detail}</span></li>)}</ol>
      </StudioPanel>
      {view.status === 'impact_ready' && selected && <StudioPanel title="Commercial impact" description="Rate-free: hours, window and open points from the price canon.">
        <ProjectCommercialImpact key={`${selected.decision_ref}:${selected.option_ref}`} projectId={projectId} revisionHash={revisionHash} decisionRef={selected.decision_ref} optionRef={selected.option_ref} />
      </StudioPanel>}
      {view.status === 'impact_ready' && selected && <StudioPanel title="Run cost" description="Capacities and licences at Microsoft list price.">
        <ProjectRunCostDelta key={`${selected.decision_ref}:${selected.option_ref}`} projectId={projectId} revisionHash={revisionHash} decisionRef={selected.decision_ref} optionRef={selected.option_ref} />
      </StudioPanel>}
      <details className={styles.details}><summary>Limitations</summary><ul className={styles.list}>{view.limitations.map(item => <li key={item}>{item}</li>)}</ul></details>
    </>}
  </section>;
}
