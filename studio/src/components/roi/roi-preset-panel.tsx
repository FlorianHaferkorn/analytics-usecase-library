'use client';

import { useState, useEffect, useCallback } from 'react';
import { StudioPanel } from '@/components/ui/studio-page';

interface RangeValue {
  min: number | string;
  likely: number | string;
  max: number | string;
  unit?: string;
  note?: string;
}

interface RoiPreset {
  kpi_id: string;
  label: string;
  baseline_range: RangeValue;
  target_range: RangeValue;
  time_horizon_months: number;
  driver_notes: string[];
}

interface Props {
  kpiId: string | null;
  kpiLabel?: string;
  golden20Ids: string[];
  onKpiChange: (kpiId: string) => void;
}

/**
 * RoiPresetPanel — Displays a min/likely/max range panel and driver notes
 * for a Golden-20 KPI preset. Fetches from /api/core/presets/[kpiId].
 */
export function RoiPresetPanel({ kpiId, kpiLabel, golden20Ids, onKpiChange }: Props) {
  const [preset, setPreset] = useState<RoiPreset | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPreset = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/core/presets/${encodeURIComponent(id)}`);
      if (!res.ok) {
        setPreset(null);
        setError(res.status === 404 ? 'No preset available for this KPI.' : 'Failed to load preset.');
        return;
      }
      const data = (await res.json()) as { preset: RoiPreset };
      setPreset(data.preset);
    } catch {
      setError('Network error loading preset.');
      setPreset(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (kpiId) void fetchPreset(kpiId);
    else setPreset(null);
  }, [kpiId, fetchPreset]);

  function formatValue(val: number | string, unit?: string): string {
    if (typeof val === 'number') {
      const isEur = unit?.toLowerCase().includes('eur') || (typeof val === 'number' && val > 1000);
      if (isEur && val >= 1000000) return `€${(val / 1000000).toFixed(1)}M`;
      if (isEur && val >= 1000) return `€${(val / 1000).toFixed(0)}k`;
      if (unit === '%' || unit?.includes('%')) return `${val}%`;
      if (unit === 'days') return `${val}d`;
      return `${val}${unit ? ` ${unit}` : ''}`;
    }
    return String(val);
  }

  return (
    <StudioPanel
      title="ROI Preset"
      description="Industry-benchmarked baseline and target ranges for the selected Golden-20 KPI."
      tone="info"
      style={{ minWidth: 300, maxWidth: 400 }}
    >
      {/* KPI selector */}
      <div style={{ padding: 'var(--gap)', borderBottom: '1px solid var(--line)' }}>
        <label
          htmlFor="roi-kpi-select"
          style={{ display: 'block', fontSize: '0.6875rem', color: 'var(--ink-3)', marginBottom: 6, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}
        >
          Golden-20 KPI
        </label>
        <select
          id="roi-kpi-select"
          value={kpiId ?? ''}
          onChange={(e) => onKpiChange(e.target.value)}
          style={{
            width: '100%',
            padding: '8px 10px',
            backgroundColor: 'var(--bg)',
            border: '1px solid var(--line)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--ink)',
            fontSize: '0.8125rem',
          }}
        >
          <option value="">— Select a KPI —</option>
          {golden20Ids.map((id) => (
            <option key={id} value={id}>{id}</option>
          ))}
        </select>
      </div>

      {/* Loading */}
      {loading && (
        <div style={{ padding: 'var(--pad)', color: 'var(--ink-3)', fontSize: '0.8125rem', textAlign: 'center' }}>
          Loading preset…
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div style={{ padding: 'var(--gap)', color: 'var(--warning)', fontSize: '0.8125rem' }}>
          {error}
        </div>
      )}

      {/* Preset content */}
      {!loading && preset && (
        <div style={{ padding: 'var(--gap)', display: 'flex', flexDirection: 'column', gap: 'var(--gap)' }}>
          <div>
            <div style={{ fontSize: '0.6875rem', color: 'var(--info)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
              {preset.label ?? kpiLabel ?? kpiId}
            </div>
            <div style={{ fontSize: '0.6875rem', color: 'var(--ink-4)' }}>
              {preset.time_horizon_months}-month horizon
            </div>
          </div>

          {/* Baseline range */}
          <RangeDisplay
            label="Baseline"
            range={preset.baseline_range}
            formatFn={formatValue}
            color="var(--ink-3)"
          />

          {/* Target range */}
          <RangeDisplay
            label="Target"
            range={preset.target_range}
            formatFn={formatValue}
            color="var(--accent)"
          />

          {/* Slider-style visual */}
          <RangeSlider
            baseline={preset.baseline_range}
            target={preset.target_range}
          />

          {/* Driver notes */}
          {preset.driver_notes && preset.driver_notes.length > 0 && (
            <div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--ink-3)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
                Key Drivers
              </div>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 4 }}>
                {preset.driver_notes.map((note, i) => (
                  <li key={i} style={{ fontSize: '0.75rem', color: 'var(--ink-2)', paddingLeft: 10, borderLeft: '2px solid var(--info)' }}>
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Note */}
          {preset.baseline_range.note && (
            <div style={{ fontSize: '0.6875rem', color: 'var(--ink-4)', fontStyle: 'italic' }}>
              {preset.baseline_range.note}
            </div>
          )}
        </div>
      )}
    </StudioPanel>
  );
}

function RangeDisplay({ label, range, formatFn, color }: {
  label: string;
  range: RangeValue;
  formatFn: (v: number | string, u?: string) => string;
  color: string;
}) {
  return (
    <div>
      <div style={{ fontSize: '0.6875rem', color, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ display: 'flex', gap: 8, fontSize: '0.8125rem' }}>
        {(['min', 'likely', 'max'] as const).map((key) => (
          <div key={key} style={{
            flex: 1,
            padding: '6px 8px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--bg)',
            border: `1px solid ${key === 'likely' ? color : 'var(--line)'}`,
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '0.5625rem', color: 'var(--ink-4)', textTransform: 'uppercase' }}>
              {key}
            </div>
            <div style={{ color, fontWeight: key === 'likely' ? 700 : 400, fontSize: '0.875rem' }}>
              {formatFn(range[key], range.unit)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function RangeSlider({ baseline, target }: { baseline: RangeValue; target: RangeValue }) {
  const bMin = Number(baseline.min);
  const bMax = Number(baseline.max);
  const tLikely = Number(target.likely);

  if (isNaN(bMin) || isNaN(bMax) || bMin === bMax) return null;

  const total = bMax - bMin;
  const tPos = Math.min(100, Math.max(0, ((tLikely - bMin) / total) * 100));
  const bLikelyPos = Math.min(100, Math.max(0, ((Number(baseline.likely) - bMin) / total) * 100));

  return (
    <div style={{ position: 'relative', height: 20, background: 'var(--panel)', borderRadius: 4, overflow: 'visible', marginTop: 4 }}>
      {/* Baseline band */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
        background: 'linear-gradient(90deg, var(--bg-2), var(--line))',
        borderRadius: 4,
      }} />
      {/* Baseline likely marker */}
      <div title={`Baseline likely: ${baseline.likely}`} style={{
        position: 'absolute', top: -2, bottom: -2, left: `${bLikelyPos}%`,
        width: 3, background: 'var(--ink-3)', borderRadius: 2,
        transform: 'translateX(-50%)',
      }} />
      {/* Target likely marker */}
      <div title={`Target: ${target.likely}`} style={{
        position: 'absolute', top: -4, bottom: -4, left: `${tPos}%`,
        width: 4, background: 'var(--accent)', borderRadius: 2,
        transform: 'translateX(-50%)',
        boxShadow: '0 0 6px var(--accent)',
      }} />
      {/* Labels */}
      <div style={{
        position: 'absolute', top: 24, left: 0, right: 0,
        display: 'flex', justifyContent: 'space-between',
        fontSize: '0.5625rem', color: 'var(--ink-4)',
      }}>
        <span>min</span><span>max</span>
      </div>
    </div>
  );
}
