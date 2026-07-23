/** Parseable discovery chat response for showcase / walkthrough (no AI required). */
export const DISCOVERY_DEMO_EXTRACTION = `strategy anchor: "Profitable growth through margin quality and price discipline"

kpi_id: margin.gm.pct
name: Gross Margin %

kpi_id: pricing.realization.pct
name: Price Realization %

action_id: ACT-COM-002-01
name: Review negative margin SKUs

UseCase scaffold:
  id: DRAFT-COM-002
  title: Margin & Price Performance (Discovery Draft)
  strategic_kpi_id: margin.gm.pct
`;

/** Minimal bracket YAML for Blueprint draft handoff demo. */
export const DISCOVERY_DEMO_SCAFFOLD = {
  draftId: 'DRAFT-COM-002',
  draftYaml: `id: DRAFT-COM-002
title: Margin & Price Performance (Discovery Draft)
domain: Commercial
documentation:
  business_factsheet: ./Business_Factsheet.md
orchestration:
  strategic_kpi_id: margin.gm.pct
  influencing_kpi_ids:
    - pricing.realization.pct
    - cost.cogs.amount
  action_code_ids:
    - ACT-COM-002-01
value_driver_model:
  impact_direction: maximize
  formula: margin.gm.pct = pricing.realization.pct + cost.cogs.amount
  impact_logic: Improve price realization while controlling COGS to expand gross margin.
`,
} as const;
