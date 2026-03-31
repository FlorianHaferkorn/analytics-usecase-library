import { Handle, Position, type NodeProps } from '@xyflow/react';

export interface StrategicKpiData {
  kpiId: string;
  label: string;
  direction: string;
  useCaseId: string;
}

export function StrategicKpiNode({ data }: NodeProps) {
  const { kpiId, label, direction, useCaseId } = data as unknown as StrategicKpiData;

  return (
    <div
      style={{
        padding: 'var(--sp-1-5) var(--sp-2)',
        backgroundColor: 'var(--slate-800)',
        border: '2px solid var(--mint)',
        borderRadius: 'var(--radius-lg)',
        minWidth: '200px',
        textAlign: 'center',
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: 'var(--mint)' }} />
      <p style={{ fontSize: '0.6875rem', color: 'var(--mint)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '2px' }}>
        Strategic KPI
      </p>
      <p style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-50)' }}>
        {label}
      </p>
      <p style={{ fontSize: '0.6875rem', fontFamily: 'var(--font-mono)', color: 'var(--slate-400)', marginTop: '2px' }}>
        {kpiId} · {direction} · {useCaseId}
      </p>
      <Handle type="source" position={Position.Bottom} style={{ background: 'var(--mint)' }} />
    </div>
  );
}
