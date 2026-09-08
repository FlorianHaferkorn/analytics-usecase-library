'use client';

import { useState, useEffect, useId } from 'react';
import { StudioButton, StudioPanel } from '@/components/ui/studio-page';
import { StudioSelect } from '@/components/ui/studio-data';
import { useProjectStore } from '@/lib/store/project-store';

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
  const projectId = useProjectStore((state) => state.projectId);
  const selectorId = useId();
  const [preset, setPreset] = useState<RoiPreset | null>(null);
  const [loading, setLoading] = useState(Boolean(kpiId));
  const [error, setError] = useState<string | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setPreset(null);
    setError(null);
    setUnavailable(false);
    setLoading(Boolean(kpiId));
    if (!kpiId) return () => controller.abort();
    async function fetchPreset() {
    try {
      const res = await fetch(`/api/core/presets/${encodeURIComponent(kpiId!)}`, { signal: controller.signal });
      if (!res.ok) {
        if (controller.signal.aborted) return;
        if (res.status === 404) setUnavailable(true);
        else setError(res.status === 401 ? 'Sign in to load these assumptions.' : res.status === 403 ? 'Your account cannot access these assumptions for this project.' : 'The assumptions could not be loaded. Try again.');
        return;
      }
      const data = (await res.json()) as { preset: RoiPreset };
      if (controller.signal.aborted) return;
      if (!data.preset?.baseline_range || !data.preset?.target_range) throw new Error('Invalid preset response');
      setPreset(data.preset);
    } catch {
      if (!controller.signal.aborted) setError('The assumptions could not be loaded. Check your connection and try again.');
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
    }
    void fetchPreset();
    return () => controller.abort();
  }, [kpiId, projectId, retry]);

  function formatValue(val: number | string, unit?: string): string {
    if (typeof val === 'number') {
      const isEur = unit?.toLowerCase() === 'eur';
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
      title="Value assumptions"
      description="Illustrative baseline and target ranges. Validate these assumptions with the customer before using them in a business case."
      tone="info"
      style={{ minWidth: 0 }}
    >
      {/* KPI selector */}
      <div style={{ padding: 'var(--gap)', borderBottom: '1px solid var(--line)' }}>
        <label
          htmlFor={selectorId}
          style={{ display: 'block', fontSize: 'var(--text-xs)', color: 'var(--ink-3)', marginBottom: 'var(--space-2)', fontWeight: 600 }}
        >
          Golden-20 KPI
        </label>
        <StudioSelect
          id={selectorId}
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
        </StudioSelect>
      </div>

      {/* Loading */}
      {loading && (
        <div role="status" style={{ padding: 'var(--pad)', color: 'var(--ink-3)', fontSize: '0.8125rem', textAlign: 'center' }}>
          Loading assumptions…
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div role="alert" style={{ padding: 'var(--gap)', color: 'var(--warning)', fontSize: '0.8125rem', display: 'grid', gap: 'var(--space-3)' }}>
          <span>{error}</span>
          <StudioButton onClick={() => setRetry((value) => value + 1)}>Try again</StudioButton>
        </div>
      )}
      {!loading && unavailable && <p role="status" style={{ padding: 'var(--gap)', color: 'var(--ink-3)', fontSize: 'var(--text-sm)' }}>No illustrative ranges are available for this KPI. Use customer evidence to define the baseline and target; no values have been assumed.</p>}
      {!kpiId && <p style={{ padding: 'var(--gap)', color: 'var(--ink-3)' }}>Select a KPI to review its available assumptions.</p>}

      {/* Preset content */}
      {!loading && preset && (
        <div style={{ padding: 'var(--gap)', display: 'flex', flexDirection: 'column', gap: 'var(--gap)' }}>
          <div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--info)', fontWeight: 700, marginBottom: 'var(--space-1)' }}>
              {preset.label ?? kpiLabel ?? kpiId}
            </div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)' }}>
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

          {/* Driver notes */}
          {preset.driver_notes && preset.driver_notes.length > 0 && (
            <div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
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
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)' }}>
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
      <div style={{ fontSize: 'var(--text-xs)', color, fontWeight: 600, marginBottom: 'var(--space-1)' }}>
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
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)' }}>
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
