import { Handle, Position, type NodeProps } from '@xyflow/react';

export interface DriverKpiData {
  kpiId: string;
  label: string;
  hasAction: boolean;
}

export function DriverKpiNode({ data }: NodeProps) {
  const { kpiId, label, hasAction } = data as unknown as DriverKpiData;
  const borderColor = hasAction ? 'var(--slate-600)' : 'var(--gold)';

  return (
    <div
      style={{
        padding: 'var(--sp-1) var(--sp-1-5)',
        backgroundColor: 'var(--slate-800)',
        border: `2px solid ${borderColor}`,
        borderRadius: 'var(--radius-md)',
        minWidth: '160px',
        textAlign: 'center',
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: borderColor }} />
      <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)', marginBottom: '2px' }}>
        Driver KPI {!hasAction && '⚠'}
      </p>
      <p style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--slate-100)' }}>
        {label}
      </p>
      <p style={{ fontSize: '0.625rem', fontFamily: 'var(--font-mono)', color: 'var(--slate-500)' }}>
        {kpiId}
      </p>
      <Handle type="source" position={Position.Bottom} style={{ background: borderColor }} />
    </div>
  );
}
