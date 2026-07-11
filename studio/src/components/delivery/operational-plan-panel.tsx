'use client';

import { StudioPanel } from '@/components/ui/studio-page';

interface Props {
  selectedCount: number;
  selectedDomains: string[];
  adapterStatus: string;
  adapterName: string;
  readinessWarnings: string[];
  runbookSteps: string[];
}

export function OperationalPlanPanel({
  selectedCount,
  selectedDomains,
  adapterStatus,
  adapterName,
  readinessWarnings,
  runbookSteps,
}: Props) {
  return (
    <StudioPanel title="Operational Plan" description="Validation checks, runbook steps and scope signals for the current delivery move." tone={readinessWarnings.length === 0 ? 'success' : 'warning'}>
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <span style={{ fontSize: '0.625rem', color: readinessWarnings.length === 0 ? 'var(--accent)' : 'var(--warning)' }}>
          {readinessWarnings.length === 0 ? 'Ready for validation' : `${readinessWarnings.length} checks before export`}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
        <div style={{ padding: '8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--panel)', border: '1px solid var(--line)' }}>
          <p style={{ fontSize: '0.625rem', color: 'var(--ink-4)', marginBottom: '2px' }}>Scope</p>
          <p style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--ink)' }}>{selectedCount}</p>
          <p style={{ fontSize: '0.625rem', color: 'var(--ink-3)' }}>use cases selected</p>
        </div>
        <div style={{ padding: '8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--panel)', border: '1px solid var(--line)' }}>
          <p style={{ fontSize: '0.625rem', color: 'var(--ink-4)', marginBottom: '2px' }}>Domains</p>
          <p style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--ink)' }}>{selectedDomains.length}</p>
          <p style={{ fontSize: '0.625rem', color: 'var(--ink-3)' }}>{selectedDomains.join(', ') || 'None'}</p>
        </div>
        <div style={{ padding: '8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--panel)', border: '1px solid var(--line)' }}>
          <p style={{ fontSize: '0.625rem', color: 'var(--ink-4)', marginBottom: '2px' }}>Target</p>
          <p style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--ink)' }}>{adapterStatus}</p>
          <p style={{ fontSize: '0.625rem', color: 'var(--ink-3)' }}>{adapterName}</p>
        </div>
      </div>

      {readinessWarnings.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {readinessWarnings.map((warning) => (
            <div key={warning} style={{ padding: '6px 8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'color-mix(in srgb, var(--warning) 10%, transparent)', border: '1px solid color-mix(in srgb, var(--warning) 24%, transparent)', fontSize: '0.6875rem', color: 'var(--warning)' }}>
              {warning}
            </div>
          ))}
        </div>
      )}

      <div>
        <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)', marginBottom: '6px' }}>Runbook</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {runbookSteps.map((step) => (
            <div key={step} style={{ padding: '8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--panel)', border: '1px solid var(--line)', fontSize: '0.6875rem', color: 'var(--ink-2)', fontFamily: 'var(--font-mono)', overflowWrap: 'anywhere' }}>
              {step}
            </div>
          ))}
        </div>
      </div>
    </StudioPanel>
  );
}
