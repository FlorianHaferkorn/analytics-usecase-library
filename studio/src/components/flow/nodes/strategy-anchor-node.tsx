import { Handle, Position, type NodeProps } from '@xyflow/react';

export interface StrategyAnchorData {
  label: string;
  description: string;
}

export function StrategyAnchorNode({ data }: NodeProps) {
  const { label, description } = data as unknown as StrategyAnchorData;

  return (
    <div
      style={{
        padding: 'var(--sp-2)',
        backgroundColor: 'var(--slate-800)',
        border: '2px solid var(--slate-400)',
        borderRadius: 'var(--radius-lg)',
        minWidth: '240px',
        textAlign: 'center',
      }}
    >
      <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '4px' }}>
        Strategy Anchor
      </p>
      <p style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--slate-50)' }}>
        {label}
      </p>
      {description && (
        <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)', marginTop: '4px' }}>
          {description}
        </p>
      )}
      <Handle type="source" position={Position.Bottom} style={{ background: 'var(--slate-400)' }} />
    </div>
  );
}
