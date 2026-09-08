'use client';

import { formatKpiValue } from '@/lib/format/kpi-value';
import { normalizeSliderRange } from '@/lib/simulation/slider-range';

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

export function KpiSlider({ kpiId, label, baseValue, value, unit, minRange, maxRange, onChange }: Props) {
  const { min, max } = normalizeSliderRange(baseValue, minRange, maxRange);
  const delta = value - baseValue;
  const format = (amount: number, displayUnit = unit) => formatKpiValue(amount, kpiId, displayUnit);

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
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-2)', marginBottom: 'var(--space-1)' }}>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-2)' }}>{label || kpiId}</span>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-2)', fontWeight: 600 }}>
          {format(value)} ({delta === 0 ? 'no change' : `${delta > 0 ? '+' : ''}${format(delta, unit === '%' ? 'pp' : unit)}`})
        </span>
      </div>

      {/* Slider + baseline tick overlay */}
      <div style={{ position: 'relative' }}>
        <input
          type="range"
          aria-label={label || kpiId}
          aria-valuetext={`${format(value)}; baseline ${format(baseValue)}`}
          title={`${kpiId}: ${format(value)}; baseline ${format(baseValue)}; range ${format(min)} to ${format(max)}`}
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
          title={`Baseline: ${format(baseValue)}`}
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

      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)' }}>
          {format(min)}
        </span>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)', fontWeight: 600 }}>
          Baseline: {format(baseValue)}
        </span>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)' }}>
          {format(max)}
        </span>
      </div>
    </div>
  );
}
