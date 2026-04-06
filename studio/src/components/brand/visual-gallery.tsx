'use client';

import type { ThemeConfig } from '@/lib/store/project-store';

interface Props {
  theme: ThemeConfig;
}

const VISUALS = ['KPI Card', 'Bar Chart', 'Line Chart', 'Waterfall', 'Detail Matrix', 'Gauge', 'Slicer', 'Scatter'];

export function VisualGallery({ theme }: Props) {
  const cssVars = {
    '--vg-primary': theme.primary,
    '--vg-secondary': theme.secondary,
    '--vg-accent': theme.accent,
    '--vg-bg': theme.background,
    '--vg-surface': theme.surface,
    '--vg-text': theme.text,
    '--vg-radius': `${Math.round(theme.borderRadius / 2)}px`,
    '--vg-font': theme.fontFamily || 'inherit',
  } as React.CSSProperties;

  return (
    <div style={{ ...cssVars } as React.CSSProperties}>
      <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 'var(--sp-1)' }}>
        Visual Gallery — {VISUALS.length} component types
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
        <GalleryCard label="KPI Card"><MiniKpiCard theme={theme} /></GalleryCard>
        <GalleryCard label="Bar Chart"><MiniBarChart /></GalleryCard>
        <GalleryCard label="Line Chart"><MiniLineChart /></GalleryCard>
        <GalleryCard label="Waterfall"><MiniWaterfall /></GalleryCard>
        <GalleryCard label="Detail Matrix"><MiniMatrix theme={theme} /></GalleryCard>
        <GalleryCard label="Gauge"><MiniGauge theme={theme} /></GalleryCard>
        <GalleryCard label="Slicer"><MiniSlicer theme={theme} /></GalleryCard>
        <GalleryCard label="Scatter"><MiniScatter /></GalleryCard>
      </div>
    </div>
  );
}

function GalleryCard({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        backgroundColor: 'var(--vg-surface)',
        borderRadius: 'var(--vg-radius)',
        border: `1px solid color-mix(in srgb, var(--vg-text) 10%, transparent)`,
        padding: '10px',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
      }}
    >
      <span
        style={{
          fontSize: '0.5rem',
          color: `color-mix(in srgb, var(--vg-text) 50%, transparent)`,
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          fontFamily: 'var(--vg-font)',
        }}
      >
        {label}
      </span>
      {children}
    </div>
  );
}

function MiniKpiCard({ theme }: { theme: ThemeConfig }) {
  return (
    <div style={{ borderLeft: '3px solid var(--vg-primary)', paddingLeft: '8px', paddingTop: '2px' }}>
      <p style={{ fontSize: '1.0625rem', fontWeight: 700, color: 'var(--vg-text)', lineHeight: 1.15, fontFamily: 'var(--vg-font)' }}>
        42.3%
      </p>
      <p style={{ fontSize: '0.5625rem', color: 'var(--vg-primary)', marginTop: '2px' }}>+1.2pp vs LY</p>
      <p style={{ fontSize: '0.5rem', color: `color-mix(in srgb, var(--vg-text) 50%, transparent)`, marginTop: '1px', fontFamily: 'var(--font-mono)' }}>
        Gross Margin
      </p>
    </div>
  );
}

function MiniBarChart() {
  const values = [28, 36, 24, 44, 32, 48, 38];
  return (
    <svg width="100%" height="44" viewBox="0 0 80 44" preserveAspectRatio="none">
      {values.map((h, i) => (
        <rect
          key={i}
          x={i * 11 + 2}
          y={44 - h * 0.85}
          width={9}
          height={h * 0.85}
          rx={2}
          fill="var(--vg-primary)"
          opacity={0.55 + i * 0.065}
        />
      ))}
    </svg>
  );
}

function MiniLineChart() {
  return (
    <svg width="100%" height="44" viewBox="0 0 80 44" preserveAspectRatio="none">
      <polyline
        points="0,36 12,26 24,30 36,16 48,20 60,10 80,6"
        fill="none"
        stroke="var(--vg-primary)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <polyline
        points="0,42 12,38 24,40 36,34 48,36 60,30 80,26"
        fill="none"
        stroke="var(--vg-secondary)"
        strokeWidth="1.5"
        strokeDasharray="3 2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Area fill */}
      <polygon
        points="0,36 12,26 24,30 36,16 48,20 60,10 80,6 80,44 0,44"
        fill="var(--vg-primary)"
        opacity={0.08}
      />
    </svg>
  );
}

function MiniWaterfall() {
  const bars = [
    { x: 3, y: 10, h: 34, fill: 'var(--vg-primary)' },
    { x: 19, y: 6, h: 14, fill: 'var(--vg-primary)' },
    { x: 35, y: 20, h: 10, fill: 'var(--vg-secondary)' },
    { x: 51, y: 28, h: 8, fill: '#ef4444' },
    { x: 67, y: 8, h: 36, fill: 'var(--vg-primary)' },
  ];
  return (
    <svg width="100%" height="44" viewBox="0 0 80 44" preserveAspectRatio="none">
      {bars.map((b, i) => (
        <rect key={i} x={b.x} y={b.y} width={12} height={b.h} rx={2} fill={b.fill} />
      ))}
    </svg>
  );
}

function MiniMatrix({ theme }: { theme: ThemeConfig }) {
  const rows = [
    { entity: 'DACH', value: '44.1%', delta: '+2.1pp', positive: true },
    { entity: 'Belux', value: '41.2%', delta: '-0.8pp', positive: false },
    { entity: 'Nordic', value: '43.5%', delta: '+1.5pp', positive: true },
  ];
  return (
    <div style={{ fontSize: '0.4875rem', lineHeight: 1.5 }}>
      {rows.map((row, i) => (
        <div
          key={i}
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr auto auto',
            gap: '4px',
            padding: '2px 0',
            borderBottom: `1px solid color-mix(in srgb, var(--vg-text) 8%, transparent)`,
            color: 'var(--vg-text)',
          }}
        >
          <span>{row.entity}</span>
          <span style={{ fontFamily: 'var(--font-mono)' }}>{row.value}</span>
          <span style={{ color: row.positive ? 'var(--vg-primary)' : '#ef4444', fontFamily: 'var(--font-mono)' }}>{row.delta}</span>
        </div>
      ))}
    </div>
  );
}

function MiniGauge({ theme }: { theme: ThemeConfig }) {
  // Arc path: semicircle 0→180 degrees
  const bg = `color-mix(in srgb, var(--vg-text) 10%, transparent)`;
  return (
    <svg width="100%" height="44" viewBox="0 0 80 48">
      {/* Track */}
      <path d="M 8 42 A 32 32 0 0 1 72 42" fill="none" stroke={bg} strokeWidth="6" strokeLinecap="round" />
      {/* Value arc ~65% of semicircle */}
      <path d="M 8 42 A 32 32 0 0 1 55 15" fill="none" stroke="var(--vg-primary)" strokeWidth="6" strokeLinecap="round" />
      <text x="40" y="45" textAnchor="middle" fontSize="11" fontWeight="700" fill="var(--vg-text)">65%</text>
    </svg>
  );
}

function MiniSlicer({ theme }: { theme: ThemeConfig }) {
  const items = ['DACH', 'Benelux', 'Nordics'];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {items.map((item, i) => (
        <div
          key={item}
          style={{
            padding: '3px 7px',
            borderRadius: 'var(--vg-radius)',
            fontSize: '0.5625rem',
            backgroundColor: i === 0 ? 'var(--vg-primary)' : `color-mix(in srgb, var(--vg-text) 6%, transparent)`,
            color: i === 0 ? theme.surface : 'var(--vg-text)',
            border: `1px solid ${i === 0 ? 'transparent' : `color-mix(in srgb, var(--vg-text) 12%, transparent)`}`,
            fontFamily: 'var(--vg-font)',
          }}
        >
          {item}
        </div>
      ))}
    </div>
  );
}

function MiniScatter() {
  const dots: [number, number, number][] = [
    [12, 36, 5], [24, 20, 4], [36, 32, 5], [48, 12, 6], [60, 28, 4],
    [20, 42, 3], [56, 38, 5], [68, 16, 6], [44, 40, 3], [8, 16, 4], [70, 36, 3],
  ];
  return (
    <svg width="100%" height="44" viewBox="0 0 80 44">
      {/* Axis lines */}
      <line x1="4" y1="40" x2="76" y2="40" stroke="var(--vg-secondary)" strokeWidth="0.5" opacity={0.4} />
      <line x1="4" y1="4" x2="4" y2="40" stroke="var(--vg-secondary)" strokeWidth="0.5" opacity={0.4} />
      {dots.map(([cx, cy, r], i) => (
        <circle
          key={i}
          cx={cx}
          cy={cy}
          r={r}
          fill="var(--vg-primary)"
          opacity={0.45 + (i % 4) * 0.15}
        />
      ))}
    </svg>
  );
}
