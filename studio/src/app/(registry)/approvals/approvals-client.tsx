'use client';

import { useState } from 'react';
import { BracketGovernancePanel } from '@/components/registry/bracket-governance-panel';

interface BracketSummary {
  id: string;
  title: string;
  domain: string;
}

interface Props {
  brackets: BracketSummary[];
}

export function ApprovalsClient({ brackets }: Props) {
  const [selectedId, setSelectedId] = useState<string | null>(brackets[0]?.id ?? null);

  return (
<<<<<<< HEAD
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 'var(--sp-3)', alignItems: 'start' }}>
=======
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 'var(--pad)', alignItems: 'start' }}>
>>>>>>> claude/implement-execution-plan-bZbSq
      {/* Bracket list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {brackets.map((b) => (
          <button
            key={b.id}
            onClick={() => setSelectedId(b.id)}
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '2px',
<<<<<<< HEAD
              padding: 'var(--sp-1-5) var(--sp-1)',
              borderRadius: 'var(--radius-md)',
              border: `1px solid ${selectedId === b.id ? 'var(--info)' : 'var(--slate-700)'}`,
              backgroundColor: selectedId === b.id ? 'color-mix(in srgb, var(--info) 10%, transparent)' : 'var(--slate-900)',
=======
              padding: '12px 8px',
              borderRadius: 'var(--radius-md)',
              border: `1px solid ${selectedId === b.id ? 'var(--info)' : 'var(--line)'}`,
              backgroundColor: selectedId === b.id ? 'color-mix(in srgb, var(--info) 10%, transparent)' : 'var(--panel)',
>>>>>>> claude/implement-execution-plan-bZbSq
              cursor: 'pointer',
              textAlign: 'left',
            }}
          >
<<<<<<< HEAD
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--slate-100)' }}>{b.id}</span>
            <span style={{ fontSize: '0.6875rem', color: 'var(--slate-400)' }}>{b.title}</span>
            <span style={{ fontSize: '0.625rem', color: 'var(--slate-600)', textTransform: 'uppercase' }}>{b.domain}</span>
=======
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--ink)' }}>{b.id}</span>
            <span style={{ fontSize: '0.6875rem', color: 'var(--ink-3)' }}>{b.title}</span>
            <span style={{ fontSize: '0.625rem', color: 'var(--ink-4)', textTransform: 'uppercase' }}>{b.domain}</span>
>>>>>>> claude/implement-execution-plan-bZbSq
          </button>
        ))}
      </div>

      {/* Governance panel */}
      <div>
        {selectedId ? (
          <BracketGovernancePanel bracketId={selectedId} />
        ) : (
<<<<<<< HEAD
          <div style={{ padding: 'var(--sp-3)', textAlign: 'center', color: 'var(--slate-500)', fontSize: '0.875rem' }}>
=======
          <div style={{ padding: 'var(--pad)', textAlign: 'center', color: 'var(--ink-4)', fontSize: '0.875rem' }}>
>>>>>>> claude/implement-execution-plan-bZbSq
            Select a bracket to view its governance state.
          </div>
        )}
      </div>
    </div>
  );
}
