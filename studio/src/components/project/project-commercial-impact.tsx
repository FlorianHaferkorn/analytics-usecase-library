'use client';

import { useEffect, useState } from 'react';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';
import type { CommercialImpact } from '@/lib/bridge/project-commercial';
import { ProjectPriceDelta } from './project-price-delta';
import styles from './project-alternative-impact.module.css';

const label = (value: string) => value.replaceAll('_', ' ');
const hours = (value: number) => `${Number(value.toFixed(2))} h`;

/** Rate-free commercial view of one alternative. Fetches only on explicit request. */
export function ProjectCommercialImpact({ projectId, revisionHash, decisionRef, optionRef }: {
  projectId: string; revisionHash: string; decisionRef: string; optionRef: string;
}) {
  const [requested, setRequested] = useState(false);
  const [result, setResult] = useState<CommercialImpact | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!requested) return;
    const abort = new AbortController();
    const query = new URLSearchParams({ revision: revisionHash, decision: decisionRef, option: optionRef });
    void fetch(`/api/projects/${encodeURIComponent(projectId)}/architecture/commercial?${query}`, { cache: 'no-store', signal: abort.signal })
      .then(async response => {
        const value = await response.json();
        if (!response.ok) throw new Error(typeof value.error === 'string' ? value.error : 'Commercial comparison unavailable');
        if (value.project_ref !== projectId || value.baseline_revision_hash !== revisionHash || value.alternative_option_ref !== optionRef || value.price_values_embedded !== false) {
          throw new Error('Commercial comparison project, revision or option mismatch');
        }
        if (!abort.signal.aborted) setResult(value as CommercialImpact);
      }).catch(reason => { if (!abort.signal.aborted) setError(reason instanceof Error ? reason.message : 'Commercial comparison unavailable'); });
    return () => abort.abort();
  }, [requested, projectId, revisionHash, decisionRef, optionRef]);

  if (!requested) {
    return <div className={styles.stack}>
      <p className={styles.note}>Runs the same alternative through the price canon on this host: hours per canon role, delivery window and open points. No rate, price or margin is shown.</p>
      <div><StudioButton onClick={() => setRequested(true)}>Evaluate against price canon</StudioButton></div>
    </div>;
  }
  if (!result) return <StudioEmptyState title={error ? 'Commercial comparison unavailable' : 'Evaluating against the price canon'} description={error || 'Reading the tenant price canon through the mirrored calculation core.'} />;
  if (result.status === 'not_checked') {
    return <StudioEmptyState title="Price canon not configured" description={`${result.reason ?? ''} Create the tenant file outside the repository with "preis_kanon_mandant.py vorlage", fill it at the Nagarro store and set PREIS_KANON_MANDANTEN_DIR on the Studio host.`} />;
  }
  if (result.status === 'tenant_findings') {
    return <StudioPanel title="Price canon has findings"><ul className={styles.list}>{(result.findings ?? []).map(item => <li key={item}>{item}</li>)}</ul></StudioPanel>;
  }
  const { delta, baseline, alternative } = result;
  if (!delta || !baseline || !alternative) return <StudioEmptyState title="Commercial comparison incomplete" description="The result did not contain both sides. Nothing is shown rather than a partial figure." />;
  const roles = Object.keys({ ...baseline.hours_by_canon_role, ...alternative.hours_by_canon_role }).sort();
  return <div className={styles.stack}>
    <table className={styles.parts}>
      <caption>Hours per canon role · accepted baseline → alternative</caption>
      <thead><tr><th scope="col">Canon role</th><th scope="col">Baseline</th><th scope="col">Alternative</th></tr></thead>
      <tbody>{roles.map(role => <tr key={role}><td>{label(role)}</td><td>{hours(baseline.hours_by_canon_role[role] ?? 0)}</td><td>{hours(alternative.hours_by_canon_role[role] ?? 0)}</td></tr>)}</tbody>
    </table>
    <dl className={styles.tiles} aria-label="Commercial summary">
      <div><dt>Window, parallel</dt><dd>{delta.window_workdays.before.parallel} → {delta.window_workdays.after.parallel} workdays</dd></div>
      <div><dt>Window, in sequence</dt><dd>{delta.window_workdays.before.serial} → {delta.window_workdays.after.serial} workdays</dd></div>
      <div><dt>New open points</dt><dd>{delta.new_gaps.length}</dd></div>
    </dl>
    {alternative.gaps.length > 0 && <StudioPanel title="Open points before the offer">
      <ul className={styles.list}>{alternative.gaps.map(gap => <li key={gap.id}><strong>{delta.new_gaps.includes(gap.id) ? 'New · ' : ''}{label(gap.id.split(':')[0])}</strong><span>{gap.detail}</span></li>)}</ul>
    </StudioPanel>}
    <StudioPanel title="Price delta (admins only)">
      <ProjectPriceDelta projectId={projectId} revisionHash={revisionHash} decisionRef={decisionRef} optionRef={optionRef} />
    </StudioPanel>
    {result.proposal_assumptions_markdown && <details className={styles.details}>
      <summary>Proposal assumptions (rate-free)</summary>
      <pre className={styles.markdown}>{result.proposal_assumptions_markdown}</pre>
    </details>}
  </div>;
}
