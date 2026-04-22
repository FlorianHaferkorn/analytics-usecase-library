'use client';

import { useState, useEffect, useCallback } from 'react';
import { StudioPanel, StudioButton, StudioEmptyState } from '@/components/ui/studio-page';

interface MetricResult {
  metric: string;
  name: string;
  score: number;
  details?: Record<string, unknown>;
}

interface ScorecardData {
  generated_at: string;
  metrics: MetricResult[];
  overall_score: number;
}

function scoreColor(score: number): string {
  if (score >= 0.8) return 'var(--success)';
  if (score >= 0.5) return 'var(--warning)';
  return 'var(--error)';
}

function MetricCard({ m }: { m: MetricResult }) {
  const pct = Math.round(m.score * 100);
  return (
    <div
      style={{
        padding: '16px',
        borderRadius: 'var(--radius-md)',
        backgroundColor: 'var(--panel)',
        border: '1px solid var(--line)',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.6875rem', color: 'var(--ink-4)', fontFamily: 'monospace' }}>{m.metric}</span>
        <span style={{ fontSize: '1rem', fontWeight: 700, color: scoreColor(m.score) }}>{pct}%</span>
      </div>
      <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--ink-2)', fontWeight: 600 }}>{m.name}</p>
      <div
        style={{
          height: '4px',
          borderRadius: '2px',
          backgroundColor: 'var(--line)',
          overflow: 'hidden',
        }}
      >
        <div style={{ width: `${pct}%`, height: '100%', backgroundColor: scoreColor(m.score), borderRadius: '2px' }} />
      </div>
    </div>
  );
}

export function HealthPageClient() {
  const [data, setData] = useState<ScorecardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/health');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json() as { data: ScorecardData };
      setData(json.data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  return (
    <StudioPanel
      title="Health Metrics"
      description="Run the scorecard to get the latest H1–H6 values. Scores update in real time."
      action={
        <StudioButton onClick={refresh} disabled={loading} tone="success" variant="primary">
          {loading ? 'Refreshing...' : 'Refresh'}
        </StudioButton>
      }
    >
      {error && (
        <div style={{ padding: '16px', backgroundColor: 'color-mix(in srgb, var(--error) 10%, transparent)', borderRadius: 'var(--radius-md)', color: 'var(--error)', fontSize: '0.875rem', marginBottom: '16px' }}>
          {error}
        </div>
      )}
      {data ? (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '16px', marginBottom: '16px' }}>
            {data.metrics.map((m) => <MetricCard key={m.metric} m={m} />)}
          </div>
          <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--ink-4)' }}>
            Overall: <strong style={{ color: scoreColor(data.overall_score) }}>{Math.round(data.overall_score * 100)}%</strong>
            {' '}· Generated {new Date(data.generated_at).toLocaleString('de-DE')}
          </p>
        </>
      ) : !loading && !error ? (
        <StudioEmptyState title="No data yet" description="Click Refresh to run the health scorecard." />
      ) : null}
    </StudioPanel>
  );
}
