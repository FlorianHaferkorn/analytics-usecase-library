// ============================================================================
// <VarianceWaterfall> — bridge chart from plan to actual with signed steps.
// ============================================================================

import type { VarianceBridge } from "../../mock/datasets.js";
import { ChartCard, ChartFrame, chartFrameBox } from "./ChartFrame.js";
import { bandScale, linearScale } from "./useScales.js";

export interface VarianceWaterfallProps {
  bridge: VarianceBridge;
  title?: string | undefined;
}

export function VarianceWaterfall({
  bridge,
  title,
}: VarianceWaterfallProps): JSX.Element {
  const box = chartFrameBox(360, 200);

  const cumulative = bridge.steps.reduce<number[]>(
    (acc, s) => [...acc, (acc[acc.length - 1] ?? bridge.anchorValue) + s.delta],
    [bridge.anchorValue],
  );
  const endValue = cumulative[cumulative.length - 1] ?? bridge.anchorValue;

  const allValues = [0, bridge.anchorValue, endValue, ...cumulative];
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const pad = (max - min) * 0.15 || 1;
  const y = linearScale([min - pad * 0.3, max + pad], [box.y1, box.y0]);

  const keys = ["anchor", ...bridge.steps.map((s) => s.id), "end"];
  const x = bandScale(keys, [box.x0, box.x1], 0.35);
  const bw = x.bandwidth();

  return (
    <ChartCard title={title ?? "Variance bridge"} subtitle={bridge.unit}>
      <ChartFrame
        vw={box.vw}
        vh={box.vh}
        yTicks={y.ticks(5)}
        yToPixel={y}
        xLabels={[bridge.anchorLabel, ...bridge.steps.map((s) => s.label), bridge.endLabel]}
        xIndexToPixel={(i) => x(keys[i]!) + bw / 2}
      >
        <rect
          x={x("anchor")}
          y={y(bridge.anchorValue)}
          width={bw}
          height={Math.max(y(0) - y(bridge.anchorValue), 1)}
          className="waterfall-anchor-bar"
        />
        <text
          x={x("anchor") + bw / 2}
          y={y(bridge.anchorValue) - 4}
          className="waterfall-step-value"
        >
          {bridge.anchorValue.toFixed(1)}
        </text>

        {bridge.steps.map((s, i) => {
          const prev = cumulative[i] ?? 0;
          const curr = cumulative[i + 1] ?? 0;
          const top = y(Math.max(prev, curr));
          const bottom = y(Math.min(prev, curr));
          const sign = s.delta >= 0 ? "+" : "";
          return (
            <g key={s.id}>
              <rect
                x={x(s.id)}
                y={top}
                width={bw}
                height={Math.max(bottom - top, 1)}
                className={`tone-fill-${s.tone}`}
              />
              <line
                className="waterfall-connector"
                x1={x(i === 0 ? "anchor" : bridge.steps[i - 1]!.id) + bw}
                x2={x(s.id)}
                y1={y(prev)}
                y2={y(prev)}
              />
              <text
                x={x(s.id) + bw / 2}
                y={top - 4}
                className="waterfall-step-value"
              >
                {sign}
                {s.delta.toFixed(1)}
              </text>
            </g>
          );
        })}

        <rect
          x={x("end")}
          y={y(endValue)}
          width={bw}
          height={Math.max(y(0) - y(endValue), 1)}
          className="waterfall-anchor-bar"
        />
        <line
          className="waterfall-connector"
          x1={x(bridge.steps[bridge.steps.length - 1]!.id) + bw}
          x2={x("end")}
          y1={y(cumulative[cumulative.length - 2] ?? endValue)}
          y2={y(cumulative[cumulative.length - 2] ?? endValue)}
        />
        <text
          x={x("end") + bw / 2}
          y={y(endValue) - 4}
          className="waterfall-step-value"
        >
          {endValue.toFixed(1)}
        </text>
      </ChartFrame>
    </ChartCard>
  );
}
