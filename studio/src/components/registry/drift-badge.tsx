'use client';

import type { DriftReport } from '@/lib/validation/drift-scanner';
import { StudioButton } from '@/components/ui/studio-page';

interface Props {
  report: DriftReport | null;
  loading: boolean;
  onClick: () => void;
}

export function DriftBadge({ report, loading, onClick }: Props) {
  if (loading) {
    return (
      <StudioButton
        onClick={onClick}
        variant="ghost"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '4px 8px',
          backgroundColor: 'var(--panel)',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--ink-3)',
          fontSize: '0.6875rem',
        }}
      >
        <span style={{ animation: 'pulse 1.5s infinite' }}>Scanning...</span>
      </StudioButton>
    );
  }

  if (!report) return null;

  const { error, warning, info } = report.counts;
  const total = error + warning + info;

  if (total === 0) {
    return (
      <StudioButton
        onClick={onClick}
        tone="success"
        variant="ghost"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '4px 8px',
          backgroundColor: 'var(--panel)',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--mint)',
          fontSize: '0.6875rem',
        }}
      >
        Integrity OK
      </StudioButton>
    );
  }

  return (
    <StudioButton
      onClick={onClick}
      tone={error > 0 ? 'warning' : 'default'}
      variant="ghost"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '4px 8px',
        backgroundColor: 'var(--panel)',
        border: `1px solid ${error > 0 ? '#EF4444' : 'var(--gold)'}`,
        borderRadius: 'var(--radius-sm)',
        fontSize: '0.6875rem',
      }}
    >
      {error > 0 && <span style={{ color: '#EF4444', fontWeight: 600 }}>{error}E</span>}
      {warning > 0 && <span style={{ color: 'var(--gold)', fontWeight: 600 }}>{warning}W</span>}
      {info > 0 && <span style={{ color: 'var(--info)', fontWeight: 600 }}>{info}I</span>}
    </StudioButton>
  );
}
