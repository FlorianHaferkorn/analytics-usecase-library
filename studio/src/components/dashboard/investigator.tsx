'use client';

import type { TrendPoint, WaterfallDriver } from '@/lib/dashboard/sample-data';

interface Props {
  label: string;
  trendData: TrendPoint[];
  waterfallData: WaterfallDriver[];
  theme?: { primary?: string; secondary?: string; surface?: string; text?: string };
}

export function Investigator({ label, trendData, waterfallData, theme }: Props) {
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-2)',
      padding: 'var(--sp-2)',
      backgroundColor: theme?.surface ?? 'var(--slate-800)',
      border: '1px solid var(--slate-700)',
      borderRadius: 'var(--radius-lg)',
    }}>
      <TrendChart label={label} data={trendData} color={theme?.primary ?? 'var(--mint)'} />
      <WaterfallChart data={waterfallData} primaryColor={theme?.primary ?? 'var(--mint)'} secondaryColor={theme?.secondary ?? 'var(--gold)'} />
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
      <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)', marginBottom: 'var(--sp-1)' }}>
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
              <text x={x + barW / 2} y={chartH + 14} textAnchor="middle" fontSize="8" fill="var(--slate-500)">
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
      <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)', marginBottom: 'var(--sp-1)' }}>
        Margin Bridge — Waterfall
      </p>
      <svg width={data.length * (barW + 8)} height={chartH + 24} style={{ display: 'block' }}>
        <line x1={0} y1={midY} x2={data.length * (barW + 8)} y2={midY} stroke="var(--slate-600)" strokeDasharray="4" />
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
              <text x={x + barW / 2} y={chartH + 14} textAnchor="middle" fontSize="8" fill="var(--slate-500)">
                {d.driver}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
