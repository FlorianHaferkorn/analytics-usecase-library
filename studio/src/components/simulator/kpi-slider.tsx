'use client';

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
  const min = minRange ?? baseValue * 0.7;
  const max = maxRange ?? baseValue * 1.3;
  const delta = value - baseValue;
  const deltaColor = delta >= 0 ? 'var(--mint)' : 'var(--danger)';

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
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--ink-2)' }}>{label || kpiId}</span>
        <span style={{ fontSize: '0.75rem', color: deltaColor, fontWeight: 600 }}>
          {value.toFixed(1)}{unit} ({delta >= 0 ? '+' : ''}{delta.toFixed(1)})
        </span>
      </div>

      {/* Slider + baseline tick overlay */}
      <div style={{ position: 'relative' }}>
        <input
          type="range"
          title={`${kpiId} — aktuell: ${value.toFixed(1)}${unit}, Baseline: ${baseValue.toFixed(1)}${unit}, Bereich: ${min.toFixed(1)}–${max.toFixed(1)}${unit}`}
          min={min}
          max={max}
          step={(max - min) / 100}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          style={{ width: '100%', accentColor: 'var(--mint)' }}
        />
        {/* T2.4: baseline tick mark — a small vertical line at the original value position */}
        <div
          aria-hidden="true"
          title={`Baseline: ${baseValue.toFixed(1)}${unit}`}
          style={{
            position: 'absolute',
            bottom: '-4px',
            left: `calc(${baselinePct}% - 1px)`,
            width: '2px',
            height: '6px',
            backgroundColor: 'var(--gold)',
            borderRadius: '1px',
            pointerEvents: 'none',
          }}
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px' }}>
        <span style={{ fontSize: '0.5625rem', color: 'var(--ink-4)' }}>
          {min.toFixed(1)}{unit}
        </span>
        <span style={{ fontSize: '0.5625rem', color: 'var(--gold)', fontWeight: 600 }}>
          ↑ base: {baseValue.toFixed(1)}{unit}
        </span>
        <span style={{ fontSize: '0.5625rem', color: 'var(--ink-4)' }}>
          {max.toFixed(1)}{unit}
        </span>
      </div>
    </div>
  );
}
