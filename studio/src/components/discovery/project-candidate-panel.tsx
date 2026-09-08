'use client';
import { useState } from 'react';
import { StudioEmptyState, StudioPanel, StudioSegmentedControl } from '@/components/ui/studio-page';
import type { DiscoveryCandidate } from '@/lib/discovery/document';
import type { ReactNode } from 'react';

export function ProjectCandidatePanel({ candidates, review }: { candidates: DiscoveryCandidate[]; review?: ReactNode }) {
  const [filter, setFilter] = useState<'all' | 'anchor' | 'kpi' | 'action'>('all');
  const filtered = filter === 'all' ? candidates : candidates.filter((candidate) => candidate.type === filter);
  return <StudioPanel title="Extracted Elements" description="Draft suggestions, not approved definitions. Verify evidence and registry meaning before adding them to the project package." bare style={{ height: '100%' }}>
    <div style={{ padding: 'var(--space-4)', borderBottom: '1px solid var(--line)' }}>
      <StudioSegmentedControl value={filter} onChange={setFilter} options={[
        { value: 'all', label: `All (${candidates.length})` }, { value: 'anchor', label: 'Anchors' }, { value: 'kpi', label: 'KPIs' }, { value: 'action', label: 'Actions' },
      ]} />
    </div>
    <div style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      {!filtered.length && <StudioEmptyState title={candidates.length ? 'No elements match the filter' : 'No extracted elements yet'} description="Ask Discovery Chat to suggest candidates from the supplied evidence. Suggestions remain a separate draft until reviewed." />}
      {filtered.map((candidate) => <details key={`${candidate.type}:${candidate.id}`} style={{ padding: 'var(--space-3)', border: '1px solid var(--line)', borderRadius: 'var(--radius-md)', overflowWrap: 'anywhere' }}>
        <summary style={{ cursor: 'pointer', color: 'var(--ink)', fontSize: 'var(--text-sm)' }}>{candidate.name} · Draft</summary>
        <dl style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-2)', display: 'grid', gap: 'var(--space-2)', marginTop: 'var(--space-3)' }}>
          <dt>Candidate reference</dt><dd>{candidate.type} · {candidate.id}</dd>
          <dt>Evidence</dt><dd>{candidate.evidenceStatus === 'quote-verified' ? 'Exact quote found in the linked source; business meaning still needs review.' : candidate.evidenceStatus === 'source-linked' ? 'Source linked; no exact supporting quote verified.' : 'Evidence not linked. Do not treat this suggestion as a requirement.'}</dd>
          <dt>Source</dt><dd>{candidate.source}{candidate.sourceId ? ` (${candidate.sourceId})` : ''}</dd>
          {candidate.sourceContext && <><dt>Verified excerpt</dt><dd>{candidate.sourceContext}</dd></>}
        </dl>
      </details>)}
      {review}
    </div>
  </StudioPanel>;
}
