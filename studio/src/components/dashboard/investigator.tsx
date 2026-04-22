'use client';

import type { TrendPoint, WaterfallDriver } from '@/lib/dashboard/sample-data';

interface Props {
  label: string;
  trendData: TrendPoint[];
  waterfallData: WaterfallDriver[];
  theme?: { primary?: string; secondary?: string; surface?: string; text?: string; background?: string; borderRadius?: number };
}

export function Investigator({ label, trendData, waterfallData, theme }: Props) {
  const radius = theme?.borderRadius != null ? `${theme.borderRadius / 2}px` : 'var(--radius-lg)';
  const borderColor = theme?.background
    ? `color-mix(in srgb, ${theme.background} 60%, ${theme.text ?? 'var(--ink-3)'})`
    : 'var(--line)';
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px',
      padding: 'var(--pad)',
      backgroundColor: theme?.surface ?? 'var(--panel)',
      border: `1px solid ${borderColor}`,
      borderRadius: radius,
    }}>
      <TrendChart label={label} data={trendData} color={theme?.primary ?? 'var(--accent)'} />
      <WaterfallChart data={waterfallData} primaryColor={theme?.primary ?? 'var(--accent)'} secondaryColor={theme?.secondary ?? 'var(--warning)'} />
    </div>
  );
}

function TrendChart({ label, data, color }: { label: string; data: TrendPoint[]; color: string }) {
  const maxVal = Math.max(...data.map((d) => d.value));
  const minVal = Math.min(...data.map((d) => d.value));
  const range = maxVal - minVal || 1;
  const chartH = 120;
  const barW = 28;

  return (
    <div>
      <p style={{ fontSize: '0.75rem', color: 'var(--ink-3)', marginBottom: '8px' }}>
        {label} — 12-Month Trend
      </p>
      <svg width={data.length * (barW + 4)} height={chartH + 24} style={{ display: 'block' }}>
        {data.map((d, i) => {
          const h = ((d.value - minVal) / range) * chartH * 0.8 + chartH * 0.1;
          const x = i * (barW + 4);
          const y = chartH - h;
          return (
            <g key={d.period}>
              <rect x={x} y={y} width={barW} height={h} rx={3} fill={color} opacity={0.7 + (i / data.length) * 0.3} />
              <text x={x + barW / 2} y={chartH + 14} textAnchor="middle" fontSize="8" fill="var(--ink-4)">
                {d.period.slice(0, 3)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function WaterfallChart({ data, primaryColor, secondaryColor }: { data: WaterfallDriver[]; primaryColor: string; secondaryColor: string }) {
  const maxAbsDelta = Math.max(...data.map((d) => Math.abs(d.delta)));
  const chartH = 120;
  const barW = 40;
  const midY = chartH / 2;

  return (
    <div>
      <p style={{ fontSize: '0.75rem', color: 'var(--ink-3)', marginBottom: '8px' }}>
        Margin Bridge — Waterfall
      </p>
      <svg width={data.length * (barW + 8)} height={chartH + 24} style={{ display: 'block' }}>
        <line x1={0} y1={midY} x2={data.length * (barW + 8)} y2={midY} stroke="var(--ink-4)" strokeDasharray="4" />
        {data.map((d, i) => {
          const h = (Math.abs(d.delta) / (maxAbsDelta || 1)) * (chartH / 2 - 10);
          const x = i * (barW + 8) + 4;
          const isPos = d.delta >= 0;
          const y = isPos ? midY - h : midY;
          const fill = isPos ? primaryColor : secondaryColor;
          return (
            <g key={d.driver}>
              <rect x={x} y={y} width={barW} height={h} rx={3} fill={fill} opacity={0.85} />
              <text x={x + barW / 2} y={isPos ? y - 4 : y + h + 12} textAnchor="middle" fontSize="9" fontWeight="600" fill={fill}>
                {isPos ? '+' : ''}{d.delta.toFixed(1)}pp
              </text>
              <text x={x + barW / 2} y={chartH + 14} textAnchor="middle" fontSize="8" fill="var(--ink-4)">
                {d.driver}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
