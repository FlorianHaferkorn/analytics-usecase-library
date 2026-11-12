// ============================================================================
// T2 · Tactical Variance page.
// ============================================================================
// Purpose (30–300s): why does plan disagree with actual? what do I do about it?
//   · KPI-Band  — EBITDA, gap, forecast accuracy
//   · Bridge    — big waterfall from plan to actual with signed deltas
//   · Drivers   — ranked driver table with tone chips & ownership
//   · Narrative — two-paragraph story accompanying the bridge
// ============================================================================

import { Canvas, Slot } from "../grid/index.js";
import {
  T2_DRIVER_ROWS,
  T2_KPIS,
  T2_VARIANCE_BRIDGE,
} from "../mock/datasets.js";
import {
  DetailMatrix,
  KpiCard,
  NarrativePanel,
  TitleBlock,
  VarianceWaterfall,
} from "../primitives/index.js";

export function T2Tactical(): JSX.Element {
  return (
    <Canvas>
      <Slot slotId="T2_Title" col={0} row={0} cs={12} rs={1.2}>
        <TitleBlock
          eyebrow="T2 · Tactical Variance"
          title="EBITDA Plan vs Actual — Q2"
          subtitle="Closed books · €M · owner column reflects accountable driver"
        />
      </Slot>

      {/* KPI band — three wider cards */}
      {T2_KPIS.map((kpi, i) => (
        <Slot
          key={kpi.id}
          slotId={`T2_KPI_${i + 1}`}
          col={i * 4}
          row={1.4}
          cs={4}
          rs={2.2}
        >
          <KpiCard data={kpi} />
        </Slot>
      ))}

      {/* Big waterfall — 8 columns */}
      <Slot slotId="T2_Waterfall" col={0} row={3.8} cs={8} rs={5.2}>
        <VarianceWaterfall
          bridge={T2_VARIANCE_BRIDGE}
          title="Variance bridge · Plan → Actual"
        />
      </Slot>

      {/* Narrative right of bridge */}
      <Slot slotId="T2_Narrative" col={8} row={3.8} cs={4} rs={5.2}>
        <NarrativePanel
          title="What changed"
          paragraphs={[
            "Volume mix and price actions combined for +€1.1M vs plan, partially offsetting an unanticipated €2.8M increase in variable COGS.",
            "FX and discretionary OpEx closed the rest of the gap. Owner actions are queued in the driver table; top priority is renegotiating logistics (Procurement).",
          ]}
        />
      </Slot>

      {/* Driver table — full width */}
      <Slot slotId="T2_Drivers" col={0} row={9.2} cs={12} rs={2.8}>
        <DetailMatrix title="Driver detail" rows={T2_DRIVER_ROWS} />
      </Slot>
    </Canvas>
  );
}

export const T2_META = {
  id: "T2",
  name: "Tactical Variance",
  description:
    "Variance layer. Answers: which drivers moved plan vs actual, by how much, and who owns the counter-action?",
} as const;
