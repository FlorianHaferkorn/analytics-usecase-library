// ============================================================================
// T4 · Prescriptive Recommendation page.
// ============================================================================
// Purpose: "what should I do next?" with quantified trade-offs.
//   · KPI-Band   — expected uplift, confidence, time-to-value
//   · Impact     — scatter of options on Impact × Effort (size = confidence)
//   · Action     — prioritized action queue
//   · Rationale  — narrative explaining the top recommendation
// ============================================================================

import { Canvas, Slot } from "../grid/index.js";
import {
  T4_ACTION_QUEUE,
  T4_IMPACT_SCATTER,
  T4_KPIS,
} from "../mock/datasets.js";
import {
  ActionQueue,
  KpiCard,
  NarrativePanel,
  ScatterChart,
  TitleBlock,
} from "../primitives/index.js";

export function T4Prescriptive(): JSX.Element {
  return (
    <Canvas>
      <Slot slotId="T4_Title" col={0} row={0} cs={12} rs={1.2}>
        <TitleBlock
          eyebrow="T4 · Prescriptive Recommendation"
          title="Growth Acceleration · Next Best Actions"
          subtitle="Scenario: Q3 push · 8 candidate actions · ranked by risk-adjusted ROI"
        />
      </Slot>

      {/* KPI band — three cards */}
      {T4_KPIS.map((kpi, i) => (
        <Slot
          key={kpi.id}
          slotId={`T4_KPI_${i + 1}`}
          col={i * 4}
          row={1.4}
          cs={4}
          rs={2.2}
        >
          <KpiCard data={kpi} />
        </Slot>
      ))}

      {/* Impact scatter — left 7 cols */}
      <Slot slotId="T4_Scatter" col={0} row={3.8} cs={7} rs={6}>
        <ScatterChart
          points={T4_IMPACT_SCATTER}
          title="Action portfolio · Impact × Effort (bubble = confidence)"
          xLabel="Effort"
          yLabel="Impact €M"
          showQuadrants
        />
      </Slot>

      {/* Action queue — right 5 cols */}
      <Slot slotId="T4_Queue" col={7} row={3.8} cs={5} rs={6}>
        <ActionQueue title="Prioritized actions" items={T4_ACTION_QUEUE} />
      </Slot>

      {/* Narrative / rationale */}
      <Slot slotId="T4_Narrative" col={0} row={9.9} cs={12} rs={2.1}>
        <NarrativePanel
          title="Rationale — top recommendation"
          paragraphs={[
            "Enterprise expansion offer leads on risk-adjusted return: 78% model confidence, ~€0.9M expected Q3 uplift, 3-week time-to-value and a named owner (Sales Ops).",
            "If the offer is sequenced with the renewal cohort launch (Action #2), cumulative Q3 impact reaches €1.6M without adding headcount. APAC channel incentive is a higher-effort/higher-variance option — hold for Q4.",
          ]}
        />
      </Slot>
    </Canvas>
  );
}

export const T4_META = {
  id: "T4",
  name: "Prescriptive Recommendation",
  description:
    "Decision layer. Answers: of all options, which action maximises risk-adjusted impact given current capacity and cost of delay?",
} as const;
