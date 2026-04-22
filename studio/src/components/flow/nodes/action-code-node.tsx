import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Warning } from '@phosphor-icons/react';
import { getStatusColor } from '@/lib/status-colors';

export interface ActionCodeData {
  actionId: string;
  label: string;
  status: string;
  domain: string;
  isOrphan?: boolean;
}

export function ActionCodeNode({ data }: NodeProps) {
  const { actionId, label, status, domain, isOrphan } = data as unknown as ActionCodeData;
  const statusColor = getStatusColor(status);
  const borderColor = isOrphan ? 'var(--danger)' : 'var(--gold)';
  const headerColor = isOrphan ? 'var(--danger)' : 'var(--gold)';

  return (
    <div
      style={{
        padding: '8px 12px',
        backgroundColor: 'var(--panel)',
        border: `2px solid ${borderColor}`,
        borderRadius: 'var(--radius-md)',
        minWidth: '160px',
        textAlign: 'center',
        boxShadow: isOrphan ? '0 0 8px 2px rgba(239, 68, 68, 0.3)' : undefined,
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: borderColor }} />
      <p style={{ fontSize: '0.6875rem', color: headerColor, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '2px' }}>
        {isOrphan ? <><Warning size={10} style={{ verticalAlign: 'middle', marginRight: '2px' }} /> Orphan Action</> : 'Action Code'}
      </p>
      <p style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
        {label}
      </p>
      <p style={{ fontSize: '0.625rem', fontFamily: 'var(--font-mono)', color: 'var(--ink-4)' }}>
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
