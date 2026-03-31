'use client';

import { useState } from 'react';
import type { EvidenceRow } from '@/lib/dashboard/sample-data';
import { tableContainerStyle, tableStyle, thStyle, tdStyle } from '@/lib/ui-styles';

const PRIORITY_COLORS: Record<string, { bg: string; text: string }> = {
  P1: { bg: 'var(--danger)', text: '#fff' },
  P2: { bg: 'var(--gold)', text: 'var(--slate-950)' },
  P3: { bg: 'var(--slate-600)', text: 'var(--slate-200)' },
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
    <div style={{
      backgroundColor: theme?.surface ?? 'var(--slate-800)',
      border: '1px solid var(--slate-700)',
      borderRadius: 'var(--radius-lg)',
      padding: 'var(--sp-2)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-1)' }}>
        <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)' }}>
          Evidence Grid — 300s Action Layer
        </p>
        <div style={{ display: 'flex', gap: 'var(--sp-1)' }}>
          {(['priority', 'delta'] as const).map((key) => (
            <button
              key={key}
              onClick={() => setSortKey(key)}
              style={{
                fontSize: '0.6875rem', padding: '2px 8px',
                backgroundColor: sortKey === key ? 'var(--slate-600)' : 'transparent',
                border: '1px solid var(--slate-600)', borderRadius: 'var(--radius-sm)',
                color: sortKey === key ? 'var(--slate-100)' : 'var(--slate-400)',
                cursor: 'pointer',
              }}
            >
              Sort: {key === 'priority' ? 'Priority' : '|Delta|'}
            </button>
          ))}
        </div>
      </div>

      <div style={tableContainerStyle}>
        <table style={tableStyle}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--slate-700)' }}>
              {['Entity', 'KPI Value', 'Delta', 'Action Code', 'Priority'].map((h) => (
                <th key={h} style={thStyle}>{h}</th>
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
                  style={{ borderBottom: '1px solid var(--slate-700)', cursor: 'pointer' }}
                >
                  <td style={{ ...tdStyle, color: 'var(--slate-100)', fontWeight: 500 }}>{row.entity}</td>
                  <td style={{ ...tdStyle, fontFamily: 'var(--font-mono)' }}>{row.kpiValue.toFixed(1)}%</td>
                  <td style={{ ...tdStyle, color: row.delta >= 0 ? 'var(--mint)' : 'var(--danger)', fontWeight: 600 }}>
                    {row.delta >= 0 ? '+' : ''}{row.delta.toFixed(1)}pp
                  </td>
                  <td style={{ ...tdStyle, fontFamily: 'var(--font-mono)', color: 'var(--gold)' }}>{row.actionCode}</td>
                  <td style={tdStyle}>
                    <span style={{
                      padding: '2px 8px', borderRadius: '9999px', fontSize: '0.625rem', fontWeight: 700,
                      backgroundColor: pc.bg, color: pc.text,
                    }}>
                      {row.priority}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
