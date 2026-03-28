'use client';

import { PulseCard } from './pulse-card';
import { Investigator } from './investigator';
import { ActionMatrix } from './action-matrix';
import { SAMPLE_KPIS, SAMPLE_TREND, SAMPLE_WATERFALL, SAMPLE_EVIDENCE } from '@/lib/dashboard/sample-data';
import type { ThemeConfig } from '@/lib/store/project-store';

interface Props {
  layer: '3s' | '30s' | '300s' | 'all';
  theme: ThemeConfig;
}

export function DashboardLayout({ layer, theme }: Props) {
  const themeProps = { primary: theme.primary, secondary: theme.secondary, surface: theme.surface, text: theme.text };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
      {(layer === '3s' || layer === 'all') && (
        <div>
          <SectionLabel>3s — Pulse</SectionLabel>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--sp-1-5)' }}>
            {SAMPLE_KPIS.map((kpi) => (
              <PulseCard key={kpi.kpiId} kpi={kpi} theme={themeProps} />
            ))}
          </div>
        </div>
      )}

      {(layer === '30s' || layer === 'all') && (
        <div>
          <SectionLabel>30s — Investigator</SectionLabel>
          <Investigator label="Gross Margin" trendData={SAMPLE_TREND} waterfallData={SAMPLE_WATERFALL} theme={themeProps} />
        </div>
      )}

      {(layer === '300s' || layer === 'all') && (
        <div>
          <SectionLabel>300s — Action Matrix</SectionLabel>
          <ActionMatrix rows={SAMPLE_EVIDENCE} theme={themeProps} />
        </div>
      )}
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 'var(--sp-1)' }}>
      {children}
    </p>
  );
}
