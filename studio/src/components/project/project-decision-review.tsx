'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';
import type { DecisionApplication, DecisionPreview } from '@/lib/bridge/project-decisions';
import styles from './project-decision-review.module.css';

function Value({ value }: { value: unknown }) {
  if (value === null || value === '') return <span className={styles.note}>Not set</span>;
  return <pre className={styles.value}>{typeof value === 'string' ? value : JSON.stringify(value, null, 2)}</pre>;
}

/** A version-keyed review. No browser-provided rule values or approval states are sent. */
export function ProjectDecisionReview({ projectId, revisionHash, onApplied }: {
  projectId: string; revisionHash: string; onApplied: (result: DecisionApplication) => void;
}) {
  const identity = `${projectId}:${revisionHash}`;
  const [preview, setPreview] = useState<DecisionPreview | null>(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [rationale, setRationale] = useState('');
  const [confirmedHash, setConfirmedHash] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const current = useRef(identity);
  useEffect(() => { current.current = identity; return () => { current.current = ''; }; }, [identity]);
  const view = preview?.project_ref === projectId && preview.revision_hash === revisionHash ? preview : null;
  const confirmed = Boolean(view && confirmedHash === view.preview_sha256);

  useEffect(() => {
    const abort = new AbortController();
    setPreview(null); setError(''); setConfirmedHash(null); setRationale(''); setBusy(false);
    void fetch(`/api/projects/${encodeURIComponent(projectId)}/architecture/decisions?revision=${revisionHash}`, { cache: 'no-store', signal: abort.signal })
      .then(async response => {
        const value = await response.json();
        if (!response.ok) throw new Error(typeof value.error === 'string' ? value.error : 'Decision review unavailable');
        if (value.project_ref !== projectId || value.revision_hash !== revisionHash) throw new Error('Decision review project or revision mismatch');
        if (!abort.signal.aborted) setPreview(value as DecisionPreview);
      }).catch(reason => { if (!abort.signal.aborted) setError(reason instanceof Error ? reason.message : 'Decision review unavailable'); });
    return () => abort.abort();
  }, [projectId, revisionHash, attempt]);

  async function apply() {
    if (!view?.can_apply || !confirmed || busy || rationale.trim().length < 20) return;
    const requested = identity;
    setBusy(true); setError('');
    try {
      const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/architecture/decisions`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ revisionHash, previewHash: view.preview_sha256, rationale: rationale.trim(), confirmed: true }),
      });
      const value = await response.json();
      if (!response.ok) throw new Error(typeof value.error === 'string' ? value.error : 'Architecture update failed');
      if (value.project_ref !== projectId || value.parent_revision_hash !== revisionHash || !/^[a-f0-9]{64}$/.test(value.revision_hash) || value.state !== 'working' || value.release_required !== true) throw new Error('Update result could not be verified. Reload the Package before continuing.');
      if (current.current === requested) onApplied(value as DecisionApplication);
    } catch (reason) {
      if (current.current === requested) { setPreview(null); setError(reason instanceof Error ? reason.message : 'Architecture update failed'); }
    } finally {
      if (current.current === requested) { setBusy(false); setConfirmedHash(null); }
    }
  }

  if (!view) return <div className={styles.stack}>
    <StudioEmptyState title={error ? 'Decision review unavailable' : 'Checking decision effects'} description={error || 'Reading the recorded rules and decision approvals for this exact version.'} />
    {error && <StudioButton onClick={() => setAttempt(n => n + 1)}>Reload decision review</StudioButton>}
  </div>;

  return <div className={styles.stack}>
    <p className={styles.note}>Only explicit, approved decision mappings can update this architecture. Review the changes below to create a new Working version. A fresh input release is required; nothing is deployed.</p>
    {view.blockers.length > 0 && <StudioPanel title="Resolve before updating"><ul className={styles.list}>{view.blockers.map((blocker, index) => <li key={`${index}:${blocker}`}>{blocker}</li>)}</ul></StudioPanel>}
    {!view.rules.length && <><StudioEmptyState title="No decision rules recorded" description="Add explicit option-to-field mappings in architecture_input.decision_rules in the Project Package. A decision's prose alone cannot safely define a workspace, tool or environment." /><Link href="/package">Open Project Package</Link></>}
    {!!view.changes.length && <section aria-label="Proposed architecture changes" className={styles.stack}>
      {view.changes.map(change => <StudioPanel key={change.rule_id} title={`${change.target.entity_id ?? change.target.collection} · ${change.target.field.replaceAll('_', ' ')}`} description={change.rationale}>
        <p className={styles.note}>Decision {change.decision_ref} · Rule {change.rule_id}</p>
        <div className={styles.comparison}>
          <div><h3>Current</h3><Value value={change.before} /></div>
          <div><h3>After update</h3><Value value={change.after} /></div>
        </div>
      </StudioPanel>)}
    </section>}
    {!!view.rules.length && <details className={styles.details}><summary>Rule evaluation · {view.rules.length} recorded</summary><ul className={styles.list}>{view.rules.map(rule => <li key={rule.id}><strong>{rule.id}</strong><span>{rule.status.replaceAll('_', ' ')} · {rule.reason}</span></li>)}</ul></details>}
    {view.can_apply && <StudioPanel title="Review and update" description="This review records the implementation rationale. It does not approve a decision on the customer's behalf.">
      <div className={styles.stack}>
        <label className={styles.field}>Review rationale<textarea value={rationale} onChange={event => { setRationale(event.target.value); setConfirmedHash(null); }} maxLength={4000} rows={3} disabled={busy} placeholder="Explain why these recorded decision effects should be applied." /></label>
        <span className={styles.note}>At least 20 characters. Do not include credentials or private rates.</span>
        <label className={styles.confirm}><input type="checkbox" checked={confirmed} disabled={busy} onChange={event => setConfirmedHash(event.target.checked ? view.preview_sha256 : null)} /> I reviewed these exact changes. Create a new Working version; do not deploy.</label>
        <div><StudioButton variant="primary" disabled={busy || !confirmed || rationale.trim().length < 20} onClick={() => void apply()}>{busy ? 'Updating architecture…' : 'Update architecture draft'}</StudioButton></div>
      </div>
    </StudioPanel>}
    {!view.can_apply && !!view.rules.length && !view.blockers.length && <p role="status" className={styles.note}>No applicable changes. Rules may already be reflected in the architecture, refer to another option, or await decision approval and confirmation. Expand the rule evaluation for each result.</p>}
  </div>;
}
