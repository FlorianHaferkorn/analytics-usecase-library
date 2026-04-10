import { Handle, Position, type NodeProps } from '@xyflow/react';

export interface StrategicKpiData {
  kpiId: string;
  kpiName: string;
  label: string;
  direction: string;
  useCaseId: string;
  domainColor?: string;
}

export function StrategicKpiNode({ data, selected }: NodeProps) {
  const { kpiName, label, direction, useCaseId, domainColor = 'var(--mint)' } = data as unknown as StrategicKpiData;

  return (
    <div
      style={{
        padding: 'var(--sp-1-5) var(--sp-2)',
        backgroundColor: selected ? `color-mix(in srgb, ${domainColor} 12%, var(--slate-800))` : 'var(--slate-800)',
        border: `2px solid ${selected ? domainColor : `color-mix(in srgb, ${domainColor} 60%, var(--slate-700))`}`,
        borderRadius: 'var(--radius-lg)',
        minWidth: '200px',
        textAlign: 'center',
        cursor: 'pointer',
        transition: 'border-color 0.15s ease, background-color 0.15s ease',
        boxShadow: selected ? `0 0 0 3px color-mix(in srgb, ${domainColor} 25%, transparent)` : undefined,
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: domainColor }} />
      <p style={{ fontSize: '0.5625rem', color: domainColor, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '2px' }}>
        Use Case · {useCaseId}
      </p>
      <p style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-50)' }}>
        {label}
      </p>
      <p style={{ fontSize: '0.6875rem', color: 'var(--slate-300)', marginTop: '3px' }}>
        {kpiName}
      </p>
      <p style={{ fontSize: '0.5625rem', color: 'var(--slate-500)', marginTop: '2px' }}>
        {direction} impact
      </p>
      <Handle type="source" position={Position.Bottom} style={{ background: domainColor }} />
    </div>
  );
}
