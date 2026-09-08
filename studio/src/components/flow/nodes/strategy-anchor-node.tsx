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
        padding: '16px',
        backgroundColor: 'var(--panel)',
        border: '2px solid var(--ink-3)',
        borderRadius: 'var(--radius-lg)',
        minWidth: '240px',
        textAlign: 'center',
      }}
    >
      <p style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-4)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '4px' }}>
        Strategy Anchor
      </p>
      <p style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--ink)' }}>
        {label}
      </p>
      {description && (
        <p style={{ fontSize: '0.75rem', color: 'var(--ink-3)', marginTop: '4px' }}>
          {description}
        </p>
      )}
      <Handle type="source" position={Position.Bottom} style={{ background: 'var(--ink-3)' }} />
    </div>
  );
}
