'use client';

import { KpiSlider } from './kpi-slider';
import { StudioButton, StudioPanel } from '@/components/ui/studio-page';

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
    <StudioPanel title="Driver Adjustments" description="Adjust illustrative values to inspect sensitivity. Slider ranges are exploration ranges, not approved business limits." style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)' }}>{drivers.length} drivers</span>
        {hasOverrides && (
          <StudioButton
            onClick={onReset}
            variant="ghost"
            style={{
              padding: '2px 8px',
              fontSize: 'var(--text-xs)',
            }}
          >
            Reset All
          </StudioButton>
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
    </StudioPanel>
  );
}
