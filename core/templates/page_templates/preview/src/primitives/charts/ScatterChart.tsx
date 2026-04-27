// ============================================================================
// <ScatterChart> — impact/effort quadrant-style bubble plot.
// ============================================================================

import type { ScatterPoint } from "../../mock/datasets.js";
import { ChartCard, ChartFrame, chartFrameBox } from "./ChartFrame.js";
import { linearScale } from "./useScales.js";

export interface ScatterChartProps {
  points: ScatterPoint[];
  title: string;
  xLabel?: string | undefined;
  yLabel?: string | undefined;
  showQuadrants?: boolean | undefined;
}

export function ScatterChart({
  points,
  title,
  xLabel,
  yLabel,
  showQuadrants = true,
}: ScatterChartProps): JSX.Element {
  const box = chartFrameBox();
  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  const sizes = points.map((p) => p.size);

  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  const yMin = Math.min(...ys);
  const yMax = Math.max(...ys);
  const xPad = (xMax - xMin) * 0.15 || 1;
  const yPad = (yMax - yMin) * 0.15 || 1;

  const xScale = linearScale([xMin - xPad, xMax + xPad], [box.x0, box.x1]);
  const yScale = linearScale([yMin - yPad, yMax + yPad], [box.y1, box.y0]);

  const sizeMax = Math.max(...sizes);
  const toRadius = (s: number): number => 2 + (s / sizeMax) * 6;

  const xMedian = median(xs);
  const yMedian = median(ys);

  return (
    <ChartCard title={title} subtitle={yLabel ? `${yLabel} vs ${xLabel ?? ""}` : undefined}>
      <ChartFrame yTicks={yScale.ticks(4)} yToPixel={yScale}>
        {showQuadrants && (
          <>
            <line
              className="chart-annotation-line"
              x1={xScale(xMedian)}
              x2={xScale(xMedian)}
              y1={box.y0}
              y2={box.y1}
            />
            <line
              className="chart-annotation-line"
              x1={box.x0}
              x2={box.x1}
              y1={yScale(yMedian)}
              y2={yScale(yMedian)}
            />
          </>
        )}

        {points.map((p) => (
          <g key={p.id}>
            <circle
              cx={xScale(p.x)}
              cy={yScale(p.y)}
              r={toRadius(p.size)}
              className={`tone-fill-${p.tone}`}
              opacity={0.6}
            />
            <circle
              cx={xScale(p.x)}
              cy={yScale(p.y)}
              r={toRadius(p.size)}
              className={`tone-stroke-${p.tone}`}
              fill="none"
              strokeWidth={1.2}
            />
          </g>
        ))}

        {xLabel && (
          <text
            x={(box.x0 + box.x1) / 2}
            y={box.vh - 4}
            textAnchor="middle"
            className="chart-axis-text"
          >
            {xLabel}
          </text>
        )}
        {yLabel && (
          <text
            x={6}
            y={(box.y0 + box.y1) / 2}
            textAnchor="middle"
            className="chart-axis-text"
            transform={`rotate(-90 6 ${(box.y0 + box.y1) / 2})`}
          >
            {yLabel}
          </text>
        )}
      </ChartFrame>
    </ChartCard>
  );
}

function median(values: number[]): number {
  const sorted = [...values].sort((a, b) => a - b);
  const n = sorted.length;
  if (n === 0) return 0;
  const mid = Math.floor(n / 2);
  if (n % 2 === 0) return ((sorted[mid - 1] ?? 0) + (sorted[mid] ?? 0)) / 2;
  return sorted[mid] ?? 0;
}
