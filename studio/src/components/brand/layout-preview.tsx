'use client';

import type { ThemeConfig } from '@/lib/store/project-store';

interface Props {
  theme: ThemeConfig;
  layer: '3s' | '30s' | '300s';
}

export function LayoutPreview({ theme, layer }: Props) {
  const layerConfig = LAYER_CONFIG[layer];

  const cssVars = {
    '--preview-primary': theme.primary,
    '--preview-secondary': theme.secondary,
    '--preview-accent': theme.accent,
    '--preview-bg': theme.background,
    '--preview-surface': theme.surface,
    '--preview-text': theme.text,
    '--preview-radius': `${Math.round(theme.borderRadius / 2)}px`,
    '--preview-font': theme.fontFamily || 'inherit',
  } as React.CSSProperties;

  return (
    <div
      style={{
        ...cssVars,
        backgroundColor: theme.background,
        borderRadius: `${theme.borderRadius}px`,
        border: '1px solid var(--line)',
        overflow: 'hidden',
        minHeight: 240,
        fontFamily: theme.fontFamily || 'inherit',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '12px 16px',
          borderBottom: `1px solid ${theme.surface}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: theme.text }}>
          {layerConfig.title}
        </span>
        <span
          style={{
            fontSize: 'var(--text-xs)',
            padding: '2px 8px',
            borderRadius: '9999px',
            backgroundColor: theme.primary,
            color: theme.surface,
            fontWeight: 600,
          }}
        >
          {layerConfig.label}
        </span>
      </div>

      {/* Content */}
      <div style={{ padding: '16px' }}>
        {layer === '3s' && <PulsePreview theme={theme} />}
        {layer === '30s' && <InvestigatorPreview theme={theme} />}
        {layer === '300s' && <ActionPreview theme={theme} />}
      </div>
    </div>
  );
}

const LAYER_CONFIG = {
  '3s': { title: 'Status Layer', label: '3s Pulse' },
  '30s': { title: 'Diagnostic Layer', label: '30s Investigator' },
  '300s': { title: 'Action Layer', label: '300s Evidence' },
} as const;

function PulsePreview({ theme }: { theme: ThemeConfig }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 140px), 1fr))', gap: 'var(--space-2)' }}>
      {['Gross Margin', 'Net Sales', 'CCC Days', 'OEE %'].map((label, i) => (
        <div
          key={label}
          style={{
            padding: '12px',
            backgroundColor: theme.surface,
            borderRadius: `${theme.borderRadius / 2}px`,
            borderLeft: `3px solid ${i === 0 ? theme.primary : i === 2 ? theme.secondary : 'var(--ink-4)'}`,
          }}
        >
          <p style={{ fontSize: 'var(--text-xs)', color: `${theme.text}88` }}>{label}</p>
          <p style={{ fontSize: '1rem', fontWeight: 700, color: theme.text, marginTop: '4px' }}>
            {['42.3%', '€4.2B', '38d', '76%'][i]}
          </p>
          <p
            style={{
              fontSize: 'var(--text-xs)',
              color: i < 2 ? theme.primary : theme.secondary,
              marginTop: '2px',
            }}
          >
            {['+1.2pp', '+5.8%', '-3d', '+2pp'][i]}
          </p>
        </div>
      ))}
    </div>
  );
}

function InvestigatorPreview({ theme }: { theme: ThemeConfig }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 200px), 1fr))', gap: 'var(--space-2)' }}>
      {/* Trend chart placeholder */}
      <div
        style={{
          padding: '12px',
          backgroundColor: theme.surface,
          borderRadius: `${theme.borderRadius / 2}px`,
          height: '100px',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <p style={{ fontSize: 'var(--text-xs)', color: `${theme.text}88`, marginBottom: '8px' }}>Trend: Net Sales</p>
        <div style={{ flex: 1, display: 'flex', alignItems: 'flex-end', gap: '3px' }}>
          {[40, 55, 48, 62, 58, 72, 68, 80, 75, 85, 78, 90].map((h, i) => (
            <div
              key={i}
              style={{
                flex: 1,
                height: `${h}%`,
                backgroundColor: theme.primary,
                borderRadius: '2px',
                opacity: 0.6 + (i / 12) * 0.4,
              }}
            />
          ))}
        </div>
      </div>

      {/* Waterfall placeholder */}
      <div
        style={{
          padding: '12px',
          backgroundColor: theme.surface,
          borderRadius: `${theme.borderRadius / 2}px`,
          height: '100px',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <p style={{ fontSize: 'var(--text-xs)', color: `${theme.text}88`, marginBottom: '8px' }}>PVM Waterfall</p>
        <div style={{ flex: 1, display: 'flex', alignItems: 'flex-end', gap: '4px', justifyContent: 'center' }}>
          {[
            { h: 70, c: theme.primary },
            { h: 25, c: theme.primary },
            { h: 15, c: theme.secondary },
            { h: 10, c: 'var(--danger)' },
            { h: 80, c: theme.primary },
          ].map((bar, i) => (
            <div
              key={i}
              style={{
                width: '24px',
                height: `${bar.h}%`,
                backgroundColor: bar.c,
                borderRadius: '2px',
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function ActionPreview({ theme }: { theme: ThemeConfig }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {/* Evidence grid placeholder */}
      <div
        style={{
          backgroundColor: theme.surface,
          borderRadius: `${theme.borderRadius / 2}px`,
          overflow: 'hidden',
        }}
      >
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', padding: '6px 12px', borderBottom: `1px solid ${theme.background}` }}>
          {['Entity', 'Margin %', 'Delta', 'Action'].map((h) => (
            <span key={h} style={{ fontSize: 'var(--text-xs)', color: `${theme.text}66`, fontWeight: 500 }}>{h}</span>
          ))}
        </div>
        {[
          ['DACH Region', '44.1%', '+2.1pp', 'C-M2.1'],
          ['Benelux', '41.2%', '-0.8pp', 'C-S1.1'],
          ['Nordics', '43.5%', '+1.5pp', '—'],
        ].map((row, i) => (
          <div key={i} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', padding: '4px 12px', borderBottom: `1px solid ${theme.background}` }}>
            {row.map((cell, j) => (
              <span
                key={j}
                style={{
                  fontSize: 'var(--text-xs)',
                  color: j === 3 ? theme.secondary : theme.text,
                  fontFamily: j > 0 ? 'var(--font-mono)' : undefined,
                }}
              >
                {cell}
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
