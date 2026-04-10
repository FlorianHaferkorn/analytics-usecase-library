import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Warning } from '@phosphor-icons/react';

export interface DriverKpiData {
  kpiId: string;
  label: string;
  hasAction: boolean;
  domainColor?: string;
}

/* T1.5: use CSS vars instead of hardcoded RGBA gold */
const pulseKeyframes = `
@keyframes actionGapPulse {
  0%, 100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--gold) 40%, transparent); }
  50% { box-shadow: 0 0 12px 4px color-mix(in srgb, var(--gold) 25%, transparent); }
}
`;

export function DriverKpiNode({ data, selected }: NodeProps) {
  const { kpiId, label, hasAction, domainColor = 'var(--slate-600)' } = data as unknown as DriverKpiData;
  const borderColor = hasAction
    ? (selected ? domainColor : `color-mix(in srgb, ${domainColor} 50%, var(--slate-700))`)
    : 'var(--gold)';

  return (
    <>
      {!hasAction && <style>{pulseKeyframes}</style>}
      <div
        style={{
          padding: 'var(--sp-1) var(--sp-1-5)',
          backgroundColor: selected ? `color-mix(in srgb, ${domainColor} 8%, var(--slate-800))` : 'var(--slate-800)',
          border: `2px solid ${borderColor}`,
          borderRadius: 'var(--radius-md)',
          minWidth: '160px',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'border-color 0.15s ease, background-color 0.15s ease',
          animation: hasAction ? undefined : 'actionGapPulse 2s ease-in-out infinite',
        }}
      >
        <Handle type="target" position={Position.Top} style={{ background: borderColor }} />
        <p style={{ fontSize: '0.5625rem', color: hasAction ? 'var(--slate-500)' : 'var(--gold)', marginBottom: '3px' }}>
          Driver KPI {!hasAction && <><Warning size={10} style={{ verticalAlign: 'middle', marginLeft: '2px' }} />No Action</>}
        </p>
        <p style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--slate-100)' }}>
          {label}
        </p>
        <p style={{ fontSize: '0.5625rem', fontFamily: 'var(--font-mono)', color: 'var(--slate-600)', marginTop: '2px' }}>
          {kpiId}
        </p>
        <Handle type="source" position={Position.Bottom} style={{ background: borderColor }} />
      </div>
    </>
  );
}
