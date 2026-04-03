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

  return (
    <div
      style={{
        padding: 'var(--sp-1) var(--sp-1-5)',
        backgroundColor: 'var(--slate-800)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--slate-700)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--slate-300)' }}>{label || kpiId}</span>
        <span style={{ fontSize: '0.75rem', color: deltaColor, fontWeight: 600 }}>
          {value.toFixed(1)}{unit} ({delta >= 0 ? '+' : ''}{delta.toFixed(1)})
        </span>
      </div>
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
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <span style={{ fontSize: '0.5625rem', color: 'var(--slate-500)' }}>
          {min.toFixed(1)}{unit}
        </span>
        <span style={{ fontSize: '0.5625rem', color: 'var(--slate-500)' }}>
          base: {baseValue.toFixed(1)}{unit}
        </span>
        <span style={{ fontSize: '0.5625rem', color: 'var(--slate-500)' }}>
          {max.toFixed(1)}{unit}
        </span>
      </div>
    </div>
  );
}
