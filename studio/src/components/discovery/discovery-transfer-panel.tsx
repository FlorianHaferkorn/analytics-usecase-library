'use client';
import { useState } from 'react';
import Link from 'next/link';
import { StudioButton } from '@/components/ui/studio-page';
import { useProjectStore } from '@/lib/store/project-store';
import type { DiscoveryCandidate } from '@/lib/discovery/document';

export function DiscoveryTransferPanel({ projectId, revision, candidates, disabled }: { projectId: string; revision: string | null; candidates: DiscoveryCandidate[]; disabled: boolean }) {
  const [open, setOpen] = useState(false);
  const [head, setHead] = useState<string | null>(null);
  const [objectives, setObjectives] = useState<string[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [objectiveKeys, setObjectiveKeys] = useState<string[]>([]);
  const [rationale, setRationale] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);
  const endpoint = `/api/projects/${encodeURIComponent(projectId)}/discovery/transfer`;
  const eligible = candidates.filter((item) => item.evidenceStatus === 'quote-verified');
  const nextObjectives = [...new Set([...objectives, ...candidates.filter((item) => objectiveKeys.includes(`${item.type}:${item.id}`)).map((item) => item.name)])];
  const review = async () => {
    setOpen(true); setBusy(true); setError(''); setDone(false); setHead(null); setConfirmed(false);
    try {
      const response = await fetch(endpoint, { cache: 'no-store' });
      const body = await response.json();
      if (!response.ok || body.projectId !== projectId) throw new Error(body.error ?? 'Could not load the current Package.');
      setHead(body.head.revision_hash); setObjectives(body.objectives);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not load the current Package.'); }
    finally { setBusy(false); }
  };
  const transfer = async () => {
    setBusy(true); setError('');
    try {
      const response = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ discoveryRevision: revision, expectedHeadRevisionHash: head, candidateKeys: selected, objectiveKeys, rationale, confirmed }) });
      const body = await response.json();
      if (!response.ok || body.projectId !== projectId) throw new Error(body.error ?? 'Transfer failed.');
      if (useProjectStore.getState().projectId === projectId) useProjectStore.getState().setPackageRevisionHash(body.revision.revision_hash);
      setDone(true); setSelected([]); setObjectiveKeys([]); setHead(null);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Transfer failed.'); }
    finally { setBusy(false); }
  };
  return <div style={{ padding: 'var(--space-3)', borderTop: '1px solid var(--line)', display: 'grid', gap: 'var(--space-2)', fontSize: 'var(--text-sm)' }}>
    <StudioButton onClick={() => void review()} disabled={disabled || !revision || !eligible.length || busy}>Review for Project Package</StudioButton>
    {!open && <p style={{ color: 'var(--ink-3)', fontSize: 'var(--text-xs)' }}>Save first. Only candidates with a verified source quote can be transferred.</p>}
    {open && <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      <StudioButton onClick={() => setOpen(false)} disabled={busy}>Close review</StudioButton>
      <p>Select proposals to preserve as evidence. Strategy anchors can also become draft project objectives. KPIs and actions require a separate governed registry mapping.</p>
      {head && <p>Reviewing Package <code>{head.slice(0, 12)}</code></p>}
      {eligible.map((item) => {
        const key = `${item.type}:${item.id}`;
        return <div key={key} style={{ display: 'grid', gap: 'var(--space-2)' }}>
          <label><input type="checkbox" checked={selected.includes(key)} disabled={busy || done} onChange={(event) => { setConfirmed(false); setSelected((previous) => event.target.checked ? [...previous, key] : previous.filter((value) => value !== key)); if (!event.target.checked) setObjectiveKeys((previous) => previous.filter((value) => value !== key)); }} /> Preserve {item.name}</label>
          <blockquote style={{ margin: 0, paddingLeft: 'var(--space-3)', color: 'var(--ink-2)' }}>{item.sourceContext} <cite>({item.source})</cite></blockquote>
          {item.type === 'anchor' && selected.includes(key) && <label><input type="checkbox" checked={objectiveKeys.includes(key)} disabled={busy || done} onChange={(event) => { setConfirmed(false); setObjectiveKeys((previous) => event.target.checked ? [...previous, key] : previous.filter((value) => value !== key)); }} /> Add as draft project objective</label>}
        </div>;
      })}
      {!!objectiveKeys.length && <section aria-label="Objective change preview" style={{ display: 'grid', gap: 'var(--space-2)', border: '1px solid var(--line)', borderRadius: 'var(--radius-md)', padding: 'var(--space-3)' }}><h4>Exact objective change</h4><p>Before</p><ul>{objectives.map((item) => <li key={item}>{item}</li>)}</ul><p>After</p><ul>{nextObjectives.map((item) => <li key={item}>{item}</li>)}</ul><p>Opportunity scope becomes Draft. Existing decisions are not changed.</p></section>}
      <label>Review rationale<textarea aria-label="Review rationale" value={rationale} maxLength={4000} disabled={busy || done} onChange={(event) => { setRationale(event.target.value); setConfirmed(false); }} style={{ width: '100%', minHeight: '5rem', background: 'var(--panel)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: 'var(--radius-md)', padding: 'var(--space-2)' }} /></label>
      <label><input type="checkbox" checked={confirmed} disabled={busy || done} onChange={(event) => setConfirmed(event.target.checked)} /> I reviewed the sources and changes. This creates a Working Package revision, not customer approval or deployment authorization.</label>
      <StudioButton variant="primary" disabled={disabled || busy || done || !head || !selected.length || rationale.trim().length < 20 || !confirmed} onClick={() => void transfer()}>Transfer reviewed selection</StudioButton>
      {done && <p role="status">Transferred to a new Working revision. <Link href="/overview">View project objectives</Link> or <Link href="/package">review the Package</Link>.</p>}
      {error && <p role="alert">{error} <StudioButton onClick={() => void review()} disabled={busy}>Reload Package review</StudioButton></p>}
    </div>}
  </div>;
}
