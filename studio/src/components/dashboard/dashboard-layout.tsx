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
  const themeProps = {
    primary: theme.primary,
    secondary: theme.secondary,
    accent: theme.accent,
    background: theme.background,
    surface: theme.surface,
    text: theme.text,
    borderRadius: theme.borderRadius,
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        backgroundColor: theme.background,
        borderRadius: `${theme.borderRadius}px`,
        fontFamily: theme.fontFamily || 'inherit',
        fontWeight: theme.fontWeight ?? 400,
        letterSpacing: theme.letterSpacing ? `${theme.letterSpacing}em` : undefined,
        lineHeight: theme.lineHeight ?? 1.5,
        padding: '16px',
        overflow: 'auto',
      }}
    >
      {(layer === '3s' || layer === 'all') && (
        <div>
          <SectionLabel color={theme.text}>3s — Pulse</SectionLabel>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
            {SAMPLE_KPIS.map((kpi) => (
              <PulseCard key={kpi.kpiId} kpi={kpi} theme={themeProps} />
            ))}
          </div>
        </div>
      )}

      {(layer === '30s' || layer === 'all') && (
        <div>
          <SectionLabel color={theme.text}>30s — Investigator</SectionLabel>
          <Investigator label="Gross Margin" trendData={SAMPLE_TREND} waterfallData={SAMPLE_WATERFALL} theme={themeProps} />
        </div>
      )}

      {(layer === '300s' || layer === 'all') && (
        <div>
          <SectionLabel color={theme.text}>300s — Action Matrix</SectionLabel>
          <ActionMatrix rows={SAMPLE_EVIDENCE} theme={themeProps} />
        </div>
      )}
    </div>
  );
}

function SectionLabel({ children, color }: { children: React.ReactNode; color?: string }) {
  return (
    <p style={{
      fontSize: 'var(--text-xs)',
      color: color ? `color-mix(in srgb, ${color} 50%, transparent)` : 'var(--ink-4)',
      textTransform: 'uppercase',
      letterSpacing: '0.1em',
      marginBottom: '8px',
    }}>
      {children}
    </p>
  );
}
