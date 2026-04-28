// ============================================================================
// <ChartFrame> — shared SVG canvas with axes & gridlines.
// ============================================================================

import type { ReactNode } from "react";
import { CHART, chartBox, type ChartBox } from "./useScales.js";

export interface ChartFrameProps {
  vw?: number | undefined;
  vh?: number | undefined;
  yTicks?: number[] | undefined;
  yToPixel?: ((v: number) => number) | undefined;
  formatY?: ((v: number) => string) | undefined;
  xLabels?: string[] | undefined;
  xIndexToPixel?: ((i: number) => number) | undefined;
  threshold?: { lower: number; upper: number } | undefined;
  annotations?: { index: number; label: string }[] | undefined;
  children?: ReactNode | undefined;
}

export function ChartFrame({
  vw = CHART.VW,
  vh = CHART.VH,
  yTicks,
  yToPixel,
  formatY = (v) => (Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(1)),
  xLabels,
  xIndexToPixel,
  threshold,
  annotations,
  children,
}: ChartFrameProps): JSX.Element {
  const box = chartBox(vw, vh);

  return (
    <svg
      className="chart-frame"
      viewBox={`0 0 ${vw} ${vh}`}
      preserveAspectRatio="none"
      role="img"
    >
      {threshold && yToPixel && (
        <rect
          className="chart-threshold-band"
          x={box.x0}
          y={yToPixel(threshold.upper)}
          width={box.innerW}
          height={Math.max(yToPixel(threshold.lower) - yToPixel(threshold.upper), 0)}
        />
      )}

      {yTicks && yToPixel && yTicks.map((t) => (
        <g key={`yt-${t}`}>
          <line
            className="chart-gridline"
            x1={box.x0}
            x2={box.x1}
            y1={yToPixel(t)}
            y2={yToPixel(t)}
          />
          <text
            className="chart-axis-text"
            x={box.x0 - 4}
            y={yToPixel(t)}
            textAnchor="end"
            dominantBaseline="middle"
          >
            {formatY(t)}
          </text>
        </g>
      ))}

      <line className="chart-axis" x1={box.x0} x2={box.x1} y1={box.y1} y2={box.y1} />

      {xLabels && xIndexToPixel && xLabels.map((label, i) => {
        const stride = computeXStride(xLabels.length);
        if (i % stride !== 0 && i !== xLabels.length - 1) return null;
        return (
          <text
            key={`xl-${i}`}
            className="chart-axis-text"
            x={xIndexToPixel(i)}
            y={box.y1 + 12}
            textAnchor="middle"
          >
            {label}
          </text>
        );
      })}

      {annotations && xIndexToPixel && annotations.map((a) => (
        <g key={`ann-${a.index}`}>
          <line
            className="chart-annotation-line"
            x1={xIndexToPixel(a.index)}
            x2={xIndexToPixel(a.index)}
            y1={box.y0}
            y2={box.y1}
          />
          <text
            className="chart-annotation-label"
            x={xIndexToPixel(a.index) + 2}
            y={box.y0 + 4}
            textAnchor="start"
            dominantBaseline="hanging"
          >
            {a.label}
          </text>
        </g>
      ))}

      {children}
    </svg>
  );
}

export function chartFrameBox(vw?: number, vh?: number): ChartBox {
  return chartBox(vw ?? CHART.VW, vh ?? CHART.VH);
}

function computeXStride(n: number): number {
  if (n <= 8) return 1;
  if (n <= 16) return 2;
  if (n <= 30) return 3;
  return Math.ceil(n / 8);
}

export interface ChartCardProps {
  title: string;
  subtitle?: string | undefined;
  children: ReactNode;
}

export function ChartCard({ title, subtitle, children }: ChartCardProps): JSX.Element {
  return (
    <div className="chart-card">
      <header className="chart-card__header">
        <h3 className="chart-card__title">{title}</h3>
        {subtitle && <span className="chart-card__sub">{subtitle}</span>}
      </header>
      <div className="chart-card__body">{children}</div>
    </div>
  );
}
