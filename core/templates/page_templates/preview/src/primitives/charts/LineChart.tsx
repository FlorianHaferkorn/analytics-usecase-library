// ============================================================================
// <LineChart> / <TrendChart> — inline SVG line chart with optional threshold
// band and annotations. TrendChart is LineChart with those extras on.
// ============================================================================

import type { TimeSeries } from "../../mock/datasets.js";
import { ChartCard, ChartFrame, chartFrameBox } from "./ChartFrame.js";
import { linearScale } from "./useScales.js";

export interface LineChartProps {
  series: TimeSeries;
  title?: string | undefined;
  showThreshold?: boolean | undefined;
  showAnnotations?: boolean | undefined;
}

export function LineChart({
  series,
  title,
  showThreshold = false,
  showAnnotations = false,
}: LineChartProps): JSX.Element {
  const box = chartFrameBox();
  const values = series.points.map((p) => p.v);
  const labels = series.points.map((p) => p.t);

  const rawMin = Math.min(...values, ...(series.threshold ? [series.threshold.lower] : []));
  const rawMax = Math.max(...values, ...(series.threshold ? [series.threshold.upper] : []));
  const pad = (rawMax - rawMin) * 0.1 || 1;
  const yDomain: [number, number] = [rawMin - pad, rawMax + pad];

  const y = linearScale(yDomain, [box.y1, box.y0]);
  const x = (i: number): number =>
    box.x0 + (i / Math.max(values.length - 1, 1)) * box.innerW;

  const path = values
    .map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(2)} ${y(v).toFixed(2)}`)
    .join(" ");

  const annotations =
    showAnnotations && series.annotations
      ? series.annotations
          .map((a) => ({ index: labels.indexOf(a.t), label: a.label }))
          .filter((a) => a.index >= 0)
      : undefined;

  return (
    <ChartCard title={title ?? series.label} subtitle={series.unit}>
      <ChartFrame
        yTicks={y.ticks(5)}
        yToPixel={y}
        xLabels={labels}
        xIndexToPixel={x}
        threshold={showThreshold ? series.threshold : undefined}
        annotations={annotations}
      >
        <path d={path} className="chart-series-line" />
        {values.map((v, i) => (
          <circle
            key={`p-${i}`}
            cx={x(i)}
            cy={y(v)}
            r={1.8}
            className="chart-series-point"
          />
        ))}
      </ChartFrame>
    </ChartCard>
  );
}

export function TrendChart(props: LineChartProps): JSX.Element {
  return <LineChart {...props} showThreshold showAnnotations />;
}
