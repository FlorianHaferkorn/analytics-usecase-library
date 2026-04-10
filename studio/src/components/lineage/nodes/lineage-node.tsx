import { Handle, Position } from '@xyflow/react';
const TYPE_STYLES: Record<string, { border: string; bg: string; icon: string }> = {
  dimension: { border: 'var(--slate-500)', bg: 'var(--slate-800)', icon: 'D' },
  fact: { border: 'var(--info)', bg: 'var(--slate-800)', icon: 'F' },
  kpi: { border: 'var(--mint)', bg: 'var(--slate-800)', icon: 'K' },
  bracket: { border: 'var(--gold)', bg: 'var(--slate-800)', icon: 'B' },
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
        padding: 'var(--sp-1) var(--sp-1-5)',
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
            color: 'var(--slate-950)',
            fontSize: '0.625rem',
            fontWeight: 700,
          }}
        >
          {style.icon}
        </span>
        <span style={{ fontSize: '0.6875rem', color: 'var(--slate-400)' }}>{nodeType}</span>
      </div>
      <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--slate-100)', lineHeight: 1.3, wordBreak: 'break-word' }}>
        {String(data.label ?? '')}
      </p>
      {typeof data.domain === 'string' && (
        <p style={{ fontSize: '0.625rem', color: 'var(--slate-500)', marginTop: '2px' }}>
          {String(data.domain)}
        </p>
      )}
      <Handle type="source" position={Position.Right} style={{ background: style.border }} />
    </div>
  );
}
