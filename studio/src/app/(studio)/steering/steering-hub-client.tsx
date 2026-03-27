'use client';

import { useMemo, useState } from 'react';
import { GoldenThreadFlow, type GoldenThreadData } from '@/components/flow/golden-thread-flow';

interface BracketData {
  id: string;
  title: string;
  domain: string;
  strategicKpiId: string;
  impactDirection: string;
  influencingKpiIds: string[];
  actionCodeIds: string[];
}

interface Props {
  strategyAnchor: string;
  brackets: BracketData[];
  actionDetails: Array<[string, { name: string; status: string; domain: string; triggerKpis: string[] }]>;
}

export function SteeringHubClient({ strategyAnchor, brackets, actionDetails }: Props) {
  const [selectedBracket, setSelectedBracket] = useState<string | null>(null);

  const flowData = useMemo<GoldenThreadData>(() => {
    const filtered = selectedBracket
      ? brackets.filter((b) => b.id === selectedBracket)
      : brackets;

    return {
      strategyAnchor,
      brackets: filtered,
      actionDetails: new Map(actionDetails),
    };
  }, [strategyAnchor, brackets, actionDetails, selectedBracket]);

  // Compute action gap stats
  const totalDrivers = brackets.reduce((sum, b) => sum + b.influencingKpiIds.length, 0);
  const actionMap = new Map(actionDetails);
  let driversWithAction = 0;
  for (const b of brackets) {
    for (const driverId of b.influencingKpiIds) {
      const hasAction = b.actionCodeIds.some((aid) => {
        const details = actionMap.get(aid);
        return details?.triggerKpis.includes(driverId);
      });
      if (hasAction) driversWithAction++;
    }
  }
  const actionGapCount = totalDrivers - driversWithAction;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)', height: 'calc(100vh - 56px - var(--sp-6))' }}>
      {/* Toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)', flexShrink: 0 }}>
        <select
          value={selectedBracket ?? ''}
          onChange={(e) => setSelectedBracket(e.target.value || null)}
          style={{
            padding: 'var(--sp-1) var(--sp-1-5)',
            backgroundColor: 'var(--slate-800)',
            border: '1px solid var(--slate-700)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--slate-100)',
            fontSize: '0.875rem',
          }}
        >
          <option value="">All Use Cases ({brackets.length})</option>
          {brackets.map((b) => (
            <option key={b.id} value={b.id}>
              {b.id} — {b.title}
            </option>
          ))}
        </select>

        <div style={{ flex: 1 }} />

        {/* Stats */}
        <div style={{ display: 'flex', gap: 'var(--sp-2)', fontSize: '0.75rem' }}>
          <span style={{ color: 'var(--mint)' }}>
            {brackets.length} Use Cases
          </span>
          <span style={{ color: 'var(--slate-400)' }}>
            {totalDrivers} Drivers
          </span>
          {actionGapCount > 0 && (
            <span style={{ color: 'var(--gold)' }}>
              {actionGapCount} Action Gaps
            </span>
          )}
        </div>
      </div>

      {/* Flow Canvas */}
      <div
        style={{
          flex: 1,
          backgroundColor: 'var(--slate-950)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--slate-700)',
          overflow: 'hidden',
        }}
      >
        <GoldenThreadFlow data={flowData} />
      </div>
    </div>
  );
}
