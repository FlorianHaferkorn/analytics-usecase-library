'use client';

import type { DriftReport } from '@/lib/validation/drift-scanner';

interface Props {
  report: DriftReport | null;
  loading: boolean;
  onClick: () => void;
}

export function DriftBadge({ report, loading, onClick }: Props) {
  if (loading) {
    return (
      <button
        onClick={onClick}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: 'var(--sp-0-5) var(--sp-1)',
          backgroundColor: 'var(--slate-800)',
          border: '1px solid var(--slate-700)',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--slate-400)',
          fontSize: '0.6875rem',
          cursor: 'pointer',
        }}
      >
        <span style={{ animation: 'pulse 1.5s infinite' }}>Scanning...</span>
      </button>
    );
  }

  if (!report) return null;

  const { error, warning, info } = report.counts;
  const total = error + warning + info;

  if (total === 0) {
    return (
      <button
        onClick={onClick}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: 'var(--sp-0-5) var(--sp-1)',
          backgroundColor: 'var(--slate-800)',
          border: '1px solid var(--slate-700)',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--mint)',
          fontSize: '0.6875rem',
          cursor: 'pointer',
        }}
      >
        Integrity OK
      </button>
    );
  }

  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: 'var(--sp-0-5) var(--sp-1)',
        backgroundColor: 'var(--slate-800)',
        border: `1px solid ${error > 0 ? '#EF4444' : 'var(--gold)'}`,
        borderRadius: 'var(--radius-sm)',
        fontSize: '0.6875rem',
        cursor: 'pointer',
      }}
    >
      {error > 0 && <span style={{ color: '#EF4444', fontWeight: 600 }}>{error}E</span>}
      {warning > 0 && <span style={{ color: 'var(--gold)', fontWeight: 600 }}>{warning}W</span>}
      {info > 0 && <span style={{ color: 'var(--info)', fontWeight: 600 }}>{info}I</span>}
    </button>
  );
}
