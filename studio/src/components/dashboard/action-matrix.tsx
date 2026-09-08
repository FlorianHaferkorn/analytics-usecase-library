'use client';

import { useState } from 'react';
import type { EvidenceRow } from '@/lib/dashboard/sample-data';
import { StudioButton, StudioPanel, StudioSegmentedControl } from '@/components/ui/studio-page';
import { StudioTable, StudioTableCell, StudioTableHeadCell, StudioTableShell } from '@/components/ui/studio-data';

const PRIORITY_COLORS: Record<string, { bg: string; text: string }> = {
  P1: { bg: 'var(--danger)', text: '#fff' },
  P2: { bg: 'var(--warning)', text: 'var(--bg)' },
  P3: { bg: 'var(--bg-2)', text: 'var(--ink-2)' },
};

interface Props {
  rows: EvidenceRow[];
  theme?: { primary?: string; surface?: string };
}

export function ActionMatrix({ rows, theme }: Props) {
  const [sortKey, setSortKey] = useState<'delta' | 'priority'>('priority');
  const [expanded, setExpanded] = useState<string | null>(null);

  const sorted = [...rows].sort((a, b) => {
    if (sortKey === 'priority') return a.priority.localeCompare(b.priority);
    return Math.abs(b.delta) - Math.abs(a.delta);
  });

  return (
    <StudioPanel
      title="Evidence Grid"
      description="300s action layer with sortable operational evidence rows."
      tone="warning"
      style={{ backgroundColor: theme?.surface ?? undefined }}
      action={
        <StudioSegmentedControl
          value={sortKey}
          onChange={setSortKey}
          options={[
            { value: 'priority', label: 'Sort: Priority' },
            { value: 'delta', label: 'Sort: |Delta|' },
          ]}
        />
      }
    >

      <StudioTableShell>
        <StudioTable>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--line)' }}>
              {['Entity', 'KPI Value', 'Delta', 'Action Code', 'Priority'].map((h) => (
                <StudioTableHeadCell key={h}>{h}</StudioTableHeadCell>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row) => {
              const pc = PRIORITY_COLORS[row.priority] ?? PRIORITY_COLORS.P3;
              return (
                <tr
                  key={row.entity}
                  onClick={() => setExpanded(expanded === row.entity ? null : row.entity)}
                  style={{ borderBottom: '1px solid var(--line)', cursor: 'pointer' }}
                >
                  <StudioTableCell style={{ color: 'var(--ink)', fontWeight: 500 }}>{row.entity}</StudioTableCell>
                  <StudioTableCell style={{ fontFamily: 'var(--font-mono)' }}>{row.kpiValue.toFixed(1)}%</StudioTableCell>
                  <StudioTableCell style={{ color: row.delta >= 0 ? 'var(--accent)' : 'var(--danger)', fontWeight: 600 }}>
                    {row.delta >= 0 ? '+' : ''}{row.delta.toFixed(1)}pp
                  </StudioTableCell>
                  <StudioTableCell style={{ fontFamily: 'var(--font-mono)', color: 'var(--warning)' }}>{row.actionCode}</StudioTableCell>
                  <StudioTableCell>
                    <span style={{
                      padding: '2px 8px', borderRadius: '9999px', fontSize: 'var(--text-xs)', fontWeight: 700,
                      backgroundColor: pc.bg, color: pc.text,
                    }}>
                      {row.priority}
                    </span>
                  </StudioTableCell>
                </tr>
              );
            })}
          </tbody>
        </StudioTable>
      </StudioTableShell>
    </StudioPanel>
  );
}
