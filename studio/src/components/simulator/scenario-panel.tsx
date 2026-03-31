'use client';

import { KpiSlider } from './kpi-slider';

interface KpiEntry {
  kpiId: string;
  label: string;
  baseValue: number;
  unit: string;
  minRange?: number;
  maxRange?: number;
}

interface Props {
  drivers: KpiEntry[];
  overrides: Map<string, number>;
  onOverride: (kpiId: string, value: number) => void;
  onReset: () => void;
}

export function ScenarioPanel({ drivers, overrides, onOverride, onReset }: Props) {
  const hasOverrides = overrides.size > 0;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--sp-1)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h4 style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--slate-100)' }}>
          Driver Adjustments
        </h4>
        {hasOverrides && (
          <button
            onClick={onReset}
            style={{
              padding: '2px var(--sp-1)',
              backgroundColor: 'transparent',
              border: '1px solid var(--slate-600)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--slate-400)',
              fontSize: '0.6875rem',
              cursor: 'pointer',
            }}
          >
            Reset All
          </button>
        )}
      </div>
      {drivers.map((d) => (
        <KpiSlider
          key={d.kpiId}
          kpiId={d.kpiId}
          label={d.label}
          baseValue={d.baseValue}
          value={overrides.get(d.kpiId) ?? d.baseValue}
          unit={d.unit}
          minRange={d.minRange}
          maxRange={d.maxRange}
          onChange={(v) => onOverride(d.kpiId, v)}
        />
      ))}
    </div>
  );
}
