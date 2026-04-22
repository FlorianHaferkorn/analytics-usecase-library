import { Handle, Position } from '@xyflow/react';
const TYPE_STYLES: Record<string, { border: string; bg: string; icon: string }> = {
  dimension: { border: 'var(--ink-4)', bg: 'var(--panel)', icon: 'D' },
  fact: { border: 'var(--info)', bg: 'var(--panel)', icon: 'F' },
  kpi: { border: 'var(--mint)', bg: 'var(--panel)', icon: 'K' },
  bracket: { border: 'var(--gold)', bg: 'var(--panel)', icon: 'B' },
};

interface Props {
  data: Record<string, unknown>;
}

export function LineageNodeComponent({ data }: Props) {
  const nodeType = String(data.type ?? 'dimension');
  const style = TYPE_STYLES[nodeType] ?? TYPE_STYLES.dimension;

  return (
    <div
      style={{
        padding: '8px 12px',
        backgroundColor: style.bg,
        border: `2px solid ${style.border}`,
        borderRadius: '8px',
        minWidth: '140px',
        maxWidth: '200px',
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: style.border }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '18px',
            height: '18px',
            borderRadius: '50%',
            backgroundColor: style.border,
            color: 'var(--ink)',
            fontSize: '0.625rem',
            fontWeight: 700,
          }}
        >
          {style.icon}
        </span>
        <span style={{ fontSize: '0.6875rem', color: 'var(--ink-3)' }}>{nodeType}</span>
      </div>
      <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--ink)', lineHeight: 1.3, wordBreak: 'break-word' }}>
        {String(data.label ?? '')}
      </p>
      {typeof data.domain === 'string' && (
        <p style={{ fontSize: '0.625rem', color: 'var(--ink-4)', marginTop: '2px' }}>
          {String(data.domain)}
        </p>
      )}
      <Handle type="source" position={Position.Right} style={{ background: style.border }} />
    </div>
  );
}
