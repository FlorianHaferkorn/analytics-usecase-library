// ============================================================================
// <ColumnChart> — vertical bars, one per category.
// <BarChart> — same but horizontal (labels on the y-axis).
// ============================================================================

import type { SeverityTone } from "../../mock/datasets.js";
import { ChartCard, ChartFrame, chartFrameBox } from "./ChartFrame.js";
import { bandScale, linearScale } from "./useScales.js";

export interface CategoryDatum {
  key: string;
  value: number;
  tone?: SeverityTone;
}

export interface ColumnChartProps {
  data: CategoryDatum[];
  title: string;
  unit?: string | undefined;
}

export function ColumnChart({ data, title, unit }: ColumnChartProps): JSX.Element {
  const box = chartFrameBox();
  const values = data.map((d) => d.value);
  const rawMin = Math.min(0, ...values);
  const rawMax = Math.max(0, ...values);
  const pad = (rawMax - rawMin) * 0.1 || 1;
  const y = linearScale([rawMin - pad * 0.1, rawMax + pad], [box.y1, box.y0]);
  const x = bandScale(
    data.map((d) => d.key),
    [box.x0, box.x1],
    0.3,
  );
  const baseline = y(0);

  return (
    <ChartCard title={title} subtitle={unit}>
      <ChartFrame
        yTicks={y.ticks(5)}
        yToPixel={y}
        xLabels={data.map((d) => d.key)}
        xIndexToPixel={(i) => x(data[i]!.key) + x.bandwidth() / 2}
      >
        {data.map((d) => {
          const top = y(Math.max(d.value, 0));
          const bottom = y(Math.min(d.value, 0));
          const toneClass = d.tone ? `tone-fill-${d.tone}` : "chart-series-bar";
          return (
            <rect
              key={d.key}
              x={x(d.key)}
              y={top}
              width={x.bandwidth()}
              height={Math.max(bottom - top, 1)}
              className={toneClass}
            />
          );
        })}
        <line
          className="chart-axis"
          x1={box.x0}
          x2={box.x1}
          y1={baseline}
          y2={baseline}
        />
      </ChartFrame>
    </ChartCard>
  );
}

export function BarChart({ data, title, unit }: ColumnChartProps): JSX.Element {
  const box = chartFrameBox(320, Math.max(140, data.length * 22 + 30));
  const values = data.map((d) => d.value);
  const rawMin = Math.min(0, ...values);
  const rawMax = Math.max(0, ...values);
  const pad = (rawMax - rawMin) * 0.1 || 1;
  const x = linearScale([rawMin - pad * 0.1, rawMax + pad], [box.x0, box.x1]);
  const y = bandScale(
    data.map((d) => d.key),
    [box.y0, box.y1],
    0.3,
  );
  const zero = x(0);

  return (
    <ChartCard title={title} subtitle={unit}>
      <ChartFrame vh={box.vh}>
        {/* Category labels (horizontal bars) */}
        {data.map((d, i) => {
          const yMid = y(d.key) + y.bandwidth() / 2;
          return (
            <text
              key={`cl-${i}`}
              x={box.x0 - 4}
              y={yMid}
              textAnchor="end"
              dominantBaseline="middle"
              className="chart-axis-text"
            >
              {d.key}
            </text>
          );
        })}
        {/* Zero baseline */}
        <line className="chart-axis" x1={zero} x2={zero} y1={box.y0} y2={box.y1} />
        {/* Bars */}
        {data.map((d) => {
          const left = x(Math.min(d.value, 0));
          const right = x(Math.max(d.value, 0));
          const toneClass = d.tone ? `tone-fill-${d.tone}` : "chart-series-bar";
          return (
            <rect
              key={d.key}
              x={left}
              y={y(d.key)}
              width={Math.max(right - left, 1)}
              height={y.bandwidth()}
              className={toneClass}
            />
          );
        })}
      </ChartFrame>
    </ChartCard>
  );
}
