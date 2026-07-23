'use client';

import { formatKpiDelta, formatKpiValue } from '@/lib/format/kpi-value';

interface Props {
  kpiId: string;
  label: string;
  baseValue: number;
  value: number;
  unit: string;
  minRange?: number;
  maxRange?: number;
  onChange: (value: number) => void;
}

export function KpiSlider({ kpiId, label, baseValue, value, minRange, maxRange, onChange }: Props) {
  const min = minRange ?? baseValue * 0.7;
  const max = maxRange ?? baseValue * 1.3;
  const delta = value - baseValue;
  const deltaColor = delta >= 0 ? 'var(--accent)' : 'var(--danger)';
  const displayValue = formatKpiValue(value, kpiId);
  const displayDelta = formatKpiDelta(delta, kpiId);
  const displayMin = formatKpiValue(min, kpiId);
  const displayMax = formatKpiValue(max, kpiId);
  const displayBase = formatKpiValue(baseValue, kpiId);

  /** T2.4: Position of baseline tick as a percentage along the slider track */
  const baselinePct = Math.max(0, Math.min(100, ((baseValue - min) / (max - min)) * 100));

  return (
    <div
      style={{
        padding: '8px var(--pad)',
        backgroundColor: 'var(--panel)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--line)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', gap: 8 }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--ink-2)', overflow: 'hidden', textOverflow: 'ellipsis' }}>{label || kpiId}</span>
        <span style={{ fontSize: '0.75rem', color: deltaColor, fontWeight: 600, whiteSpace: 'nowrap' }}>
          {displayValue} ({displayDelta})
        </span>
      </div>

      {/* Slider + baseline tick overlay */}
      <div style={{ position: 'relative' }}>
        <input
          type="range"
          title={`${kpiId} — aktuell: ${displayValue}, Baseline: ${displayBase}, Bereich: ${displayMin}–${displayMax}`}
          min={min}
          max={max}
          step={(max - min) / 100}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          style={{ width: '100%', accentColor: 'var(--accent)' }}
        />
        {/* T2.4: baseline tick mark — a small vertical line at the original value position */}
        <div
          aria-hidden="true"
          title={`Baseline: ${displayBase}`}
          style={{
            position: 'absolute',
            bottom: '-4px',
            left: `calc(${baselinePct}% - 1px)`,
            width: '2px',
            height: '6px',
            backgroundColor: 'var(--warning)',
            borderRadius: '1px',
            pointerEvents: 'none',
          }}
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', gap: 8 }}>
        <span style={{ fontSize: '0.5625rem', color: 'var(--ink-4)' }}>
          {displayMin}
        </span>
        <span style={{ fontSize: '0.5625rem', color: 'var(--warning)', fontWeight: 600 }}>
          ↑ base: {displayBase}
        </span>
        <span style={{ fontSize: '0.5625rem', color: 'var(--ink-4)' }}>
          {displayMax}
        </span>
      </div>
    </div>
  );
}
