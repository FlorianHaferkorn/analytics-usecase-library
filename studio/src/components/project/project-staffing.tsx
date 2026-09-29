'use client';

import { useEffect, useState } from 'react';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';
import type { StaffingResult } from '@/lib/bridge/project-staffing';
import styles from './project-alternative-impact.module.css';

const label = (value: string) => value.replaceAll('_', ' ');
const num = (value: number) => `${Number(value.toFixed(2))}`;

/** Named staffing of one alternative. Admin only, fetched on explicit request, never stored. */
export function ProjectStaffing({ projectId, revisionHash, decisionRef, optionRef }: {
  projectId: string; revisionHash: string; decisionRef: string; optionRef: string;
}) {
  const [requested, setRequested] = useState(false);
  const [result, setResult] = useState<StaffingResult | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!requested) return;
    const abort = new AbortController();
    const query = new URLSearchParams({ revision: revisionHash, decision: decisionRef, option: optionRef });
    void fetch(`/api/projects/${encodeURIComponent(projectId)}/architecture/commercial/staffing?${query}`, { cache: 'no-store', signal: abort.signal })
      .then(async response => {
        const value = await response.json();
        if (response.status === 403) throw new Error('Only project admins can see named staffing.');
        if (!response.ok) throw new Error(typeof value.error === 'string' ? value.error : 'Staffing unavailable');
        if (value.project_ref !== projectId || value.baseline_revision_hash !== revisionHash || value.alternative_option_ref !== optionRef || value.persist !== false) {
          throw new Error('Staffing project, revision or option mismatch');
        }
        if (!abort.signal.aborted) setResult(value as StaffingResult);
      }).catch(reason => { if (!abort.signal.aborted) setError(reason instanceof Error ? reason.message : 'Staffing unavailable'); });
    return () => abort.abort();
  }, [requested, projectId, revisionHash, decisionRef, optionRef]);

  if (!requested) {
    return <div className={styles.stack}>
      <p className={styles.note}>Admins only: who of the roster carries the hours of the alternative, and for how many weeks. Names are shown here, never stored or exported.</p>
      <div><StudioButton onClick={() => setRequested(true)}>Show named staffing</StudioButton></div>
    </div>;
  }
  if (!result) return <StudioEmptyState title={error ? 'Staffing unavailable' : 'Matching the roster'} description={error || 'Putting roster names against the canon hours.'} />;
  if (result.status !== 'evaluated' || !result.alternative || !result.delta) {
    return <StudioEmptyState title="No named staffing" description={result.reason ?? ((result.findings ?? []).join(' · ') || 'The roster could not be evaluated.')} />;
  }
  const { alternative, delta } = result;
  return <div className={styles.stack}>
    <table className={styles.parts}>
      <caption>Named staffing · alternative ({num(delta.weeks_in_parallel.before)} → {num(delta.weeks_in_parallel.after)} weeks in parallel)</caption>
      <thead><tr><th scope="col">Role and location</th><th scope="col">Hours</th><th scope="col">Weeks</th><th scope="col">People</th></tr></thead>
      <tbody>{alternative.classes.map(row => <tr key={row.rate_class}>
        <td>{label(row.rate_class)}</td><td>{num(row.hours)} h</td><td>{num(row.weeks)}</td>
        <td>{row.people.map(person => `${person.name} (${num(person.hours)} h)`).join(', ')}</td>
      </tr>)}</tbody>
    </table>
    {(delta.people_no_longer_needed.length > 0 || delta.people_newly_needed.length > 0) && <p className={styles.note}>
      {delta.people_no_longer_needed.length > 0 && `No longer needed: ${delta.people_no_longer_needed.join(', ')}. `}
      {delta.people_newly_needed.length > 0 && `Newly needed: ${delta.people_newly_needed.join(', ')}.`}
    </p>}
    {alternative.gaps.length > 0 && <StudioPanel title="Nobody on the roster">
      <ul className={styles.list}>{alternative.gaps.map(gap => <li key={gap.rate_class}><strong>{label(gap.rate_class)}</strong><span>{num(gap.hours)} h · {gap.detail}</span></li>)}</ul>
    </StudioPanel>}
  </div>;
}
