import { Handle, Position, type NodeProps } from '@xyflow/react';

export interface DriverKpiData {
  kpiId: string;
  label: string;
  hasAction: boolean;
}

const pulseKeyframes = `
@keyframes actionGapPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 184, 0, 0.4); }
  50% { box-shadow: 0 0 12px 4px rgba(255, 184, 0, 0.25); }
}
`;

export function DriverKpiNode({ data }: NodeProps) {
  const { kpiId, label, hasAction } = data as unknown as DriverKpiData;
  const borderColor = hasAction ? 'var(--slate-600)' : 'var(--gold)';

  return (
    <>
      {!hasAction && <style>{pulseKeyframes}</style>}
      <div
        style={{
          padding: 'var(--sp-1) var(--sp-1-5)',
          backgroundColor: 'var(--slate-800)',
          border: `2px solid ${borderColor}`,
          borderRadius: 'var(--radius-md)',
          minWidth: '160px',
          textAlign: 'center',
          animation: hasAction ? undefined : 'actionGapPulse 2s ease-in-out infinite',
        }}
      >
        <Handle type="target" position={Position.Top} style={{ background: borderColor }} />
        <p style={{ fontSize: '0.6875rem', color: hasAction ? 'var(--slate-500)' : 'var(--gold)', marginBottom: '2px' }}>
          Driver KPI {!hasAction && '⚠ No Action'}
        </p>
        <p style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--slate-100)' }}>
          {label}
        </p>
        <p style={{ fontSize: '0.625rem', fontFamily: 'var(--font-mono)', color: 'var(--slate-500)' }}>
          {kpiId}
        </p>
        <Handle type="source" position={Position.Bottom} style={{ background: borderColor }} />
      </div>
    </>
  );
}
