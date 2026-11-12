// ============================================================================
// <KpiCard> — Label, big value, delta chip, sparkline.
// ============================================================================
// All dimensions come from tokens. Sparkline is inline SVG with a viewBox,
// so it re-scales with container size and typography scale automatically.
// ============================================================================

import type { KpiDatum } from "../mock/datasets.js";
import "./primitives.css";

export interface KpiCardProps {
  data: KpiDatum;
}

export function KpiCard({ data }: KpiCardProps): JSX.Element {
  const {
    label,
    valueFormatted,
    deltaPct,
    direction,
    tone,
    target,
    sparkline,
  } = data;

  const deltaSign = deltaPct > 0 ? "+" : deltaPct < 0 ? "" : "±";
  const deltaFormatted =
    direction === "flat" ? "±0.0%" : `${deltaSign}${(deltaPct * 100).toFixed(1)}%`;

  return (
    <div className="kpi-card">
      <p className="kpi-card__label">{label}</p>
      <div className="kpi-card__value-row">
        <span className="kpi-card__value">{valueFormatted}</span>
        <span className={`kpi-card__delta tone-${tone}`}>{deltaFormatted}</span>
        {target !== undefined && (
          <span className="kpi-card__target">Target {formatTarget(target, data.unit)}</span>
        )}
      </div>
      <Sparkline values={sparkline} tone={tone} />
    </div>
  );
}

function formatTarget(v: number, unit: string): string {
  if (unit === "%") return `${v}%`;
  if (unit === "×") return `${v}×`;
  if (unit === "€M") return `€${v}M`;
  if (unit === "h") return `${v} h`;
  return `${v}${unit ? " " + unit : ""}`;
}

// ---- Sparkline ------------------------------------------------------------

interface SparklineProps {
  values: number[];
  tone: KpiDatum["tone"];
}

function Sparkline({ values, tone }: SparklineProps): JSX.Element {
  // Render into a 100×30 viewBox — CSS stretches it to fit the card.
  const W = 100;
  const H = 30;
  const PAD = 2;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = (W - 2 * PAD) / Math.max(values.length - 1, 1);

  const toX = (i: number): number => PAD + i * step;
  const toY = (v: number): number => H - PAD - ((v - min) / range) * (H - 2 * PAD);

  const path = values
    .map((v, i) => `${i === 0 ? "M" : "L"}${toX(i).toFixed(2)} ${toY(v).toFixed(2)}`)
    .join(" ");

  const lastX = toX(values.length - 1);
  const lastY = toY(values[values.length - 1] ?? 0);

  return (
    <svg
      className="kpi-card__sparkline"
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path d={path} className={`tone-stroke-${tone}`} fill="none" strokeWidth={1.5} />
      <circle cx={lastX} cy={lastY} r={2} className={`tone-fill-${tone}`} />
    </svg>
  );
}
