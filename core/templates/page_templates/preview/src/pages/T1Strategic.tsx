// ============================================================================
// T1 · Strategic Overview page.
// ============================================================================
// Purpose (3–30s scan): executive answer at a glance.
//   · KPI-Band  — five headline metrics with delta & sparkline
//   · Trend     — revenue trend with threshold band & annotations
//   · Variance  — plan-vs-actual bridge
//   · Drivers   — segment breakdown table
//   · Action    — what's next, who owns it
// ============================================================================

import { Canvas, Slot } from "../grid/index.js";
import {
  T1_KPIS,
  T1_REVENUE_TREND,
  T1_DRIVER_ROWS,
  T2_VARIANCE_BRIDGE,
  T4_ACTION_QUEUE,
} from "../mock/datasets.js";
import {
  ActionQueue,
  DetailMatrix,
  KpiCard,
  NarrativePanel,
  TitleBlock,
  TrendChart,
  VarianceWaterfall,
} from "../primitives/index.js";

export function T1Strategic(): JSX.Element {
  return (
    <Canvas>
      {/* Title band */}
      <Slot slotId="T1_Title" col={0} row={0} cs={12} rs={1.2}>
        <TitleBlock
          eyebrow="T1 · Strategic Overview"
          title="Revenue, Margin & Commercial Health — YTD"
          subtitle="As of close of business · Source: Finance Mart · Refresh 06:00 UTC"
        />
      </Slot>

      {/* KPI band — five cards, each 2.4 columns */}
      {T1_KPIS.map((kpi, i) => (
        <Slot
          key={kpi.id}
          slotId={`T1_KPI_${i + 1}`}
          col={i * 2.4}
          row={1.4}
          cs={2.4}
          rs={2.2}
        >
          <KpiCard data={kpi} />
        </Slot>
      ))}

      {/* Trend chart (left half) */}
      <Slot slotId="T1_Trend" col={0} row={3.8} cs={6} rs={5}>
        <TrendChart series={T1_REVENUE_TREND} title="Revenue trend — YTD" />
      </Slot>

      {/* Variance waterfall (right half) */}
      <Slot slotId="T1_Variance" col={6} row={3.8} cs={6} rs={5}>
        <VarianceWaterfall
          bridge={T2_VARIANCE_BRIDGE}
          title="Plan → Actual bridge (EBITDA)"
        />
      </Slot>

      {/* Driver matrix (bottom left 8) */}
      <Slot slotId="T1_Drivers" col={0} row={8.9} cs={8} rs={3.1}>
        <DetailMatrix title="Segment breakdown" rows={T1_DRIVER_ROWS} />
      </Slot>

      {/* Action queue (bottom right 4) */}
      <Slot slotId="T1_Action" col={8} row={8.9} cs={4} rs={3.1}>
        <ActionQueue title="Recommended actions" items={T4_ACTION_QUEUE.slice(0, 3)} />
      </Slot>
    </Canvas>
  );
}

export const T1_META = {
  id: "T1",
  name: "Strategic Overview",
  description:
    "Executive scan layer. Answers: where are we on revenue, margin and commercial health — and where is plan drifting?",
} as const;

export function T1Narrative(): JSX.Element {
  return (
    <NarrativePanel
      title="Narrative"
      paragraphs={[
        "Revenue is tracking €54.2M YTD, +6.3% vs plan driven by Enterprise renewals and a stronger-than-modelled APAC uplift.",
        "Margin has softened to 62.1% (−1.9pp vs plan) as onboarding-led COGS and partner fees absorbed the mix benefit. NPS holds at 42.",
      ]}
    />
  );
}
