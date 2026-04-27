// ============================================================================
// T3 · Operational Monitoring page.
// ============================================================================
// Purpose (minute-by-minute control loop): is the system in-band right now?
//   · Status-Tiles — OEE, OTD, scrap rate, downtime
//   · Throughput   — 14-day line with anomaly annotations & threshold band
//   · Line Detail  — per-line performance matrix with ownership
// ============================================================================

import { Canvas, Slot } from "../grid/index.js";
import {
  T3_DETAIL_ROWS,
  T3_STATUS_TILES,
  T3_THROUGHPUT_SERIES,
} from "../mock/datasets.js";
import {
  DetailMatrix,
  KpiCard,
  TitleBlock,
  TrendChart,
} from "../primitives/index.js";

export function T3Operational(): JSX.Element {
  return (
    <Canvas>
      <Slot slotId="T3_Title" col={0} row={0} cs={12} rs={1.2}>
        <TitleBlock
          eyebrow="T3 · Operational Monitoring"
          title="Plant Floor · Production Health"
          subtitle="Real-time · 14-day rolling window · auto-refresh every 60s"
        />
      </Slot>

      {/* Status tiles — four cards */}
      {T3_STATUS_TILES.map((kpi, i) => (
        <Slot
          key={kpi.id}
          slotId={`T3_Tile_${i + 1}`}
          col={i * 3}
          row={1.4}
          cs={3}
          rs={2.4}
        >
          <KpiCard data={kpi} />
        </Slot>
      ))}

      {/* Throughput trend — full width */}
      <Slot slotId="T3_Throughput" col={0} row={4} cs={12} rs={4.8}>
        <TrendChart
          series={T3_THROUGHPUT_SERIES}
          title="Throughput · units/h (threshold & anomalies)"
        />
      </Slot>

      {/* Line detail — full width */}
      <Slot slotId="T3_Detail" col={0} row={8.9} cs={12} rs={3.1}>
        <DetailMatrix
          title="Line-level performance"
          rows={T3_DETAIL_ROWS}
          actualLabel="Actual (units/h)"
          planLabel="Target"
        />
      </Slot>
    </Canvas>
  );
}

export const T3_META = {
  id: "T3",
  name: "Operational Monitoring",
  description:
    "Control-loop layer. Answers: are the lines running in-band, where did we breach, and which shift owns recovery?",
} as const;
