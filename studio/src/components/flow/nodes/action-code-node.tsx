import { Handle, Position, type NodeProps } from '@xyflow/react';

export interface ActionCodeData {
  actionId: string;
  label: string;
  status: string;
  domain: string;
}

export function ActionCodeNode({ data }: NodeProps) {
  const { actionId, label, status, domain } = data as unknown as ActionCodeData;
  const statusColor =
    status === 'active' ? 'var(--mint)' : status === 'draft' ? 'var(--gold)' : 'var(--slate-500)';

  return (
    <div
      style={{
        padding: 'var(--sp-1) var(--sp-1-5)',
        backgroundColor: 'var(--slate-800)',
        border: '2px solid var(--gold)',
        borderRadius: 'var(--radius-md)',
        minWidth: '160px',
        textAlign: 'center',
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: 'var(--gold)' }} />
      <p style={{ fontSize: '0.6875rem', color: 'var(--gold)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '2px' }}>
        Action Code
      </p>
      <p style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--slate-100)' }}>
        {label}
      </p>
      <p style={{ fontSize: '0.625rem', fontFamily: 'var(--font-mono)', color: 'var(--slate-500)' }}>
        {actionId} · {domain}
      </p>
      <span
        style={{
          display: 'inline-block',
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: statusColor,
          marginTop: '4px',
        }}
      />
    </div>
  );
}
