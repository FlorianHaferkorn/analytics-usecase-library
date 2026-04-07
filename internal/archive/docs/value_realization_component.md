---
id: value_realization_component
factsheet_type: design_spec
owner_role: Analytics Product Owner
steward_role: BI Engineering Lead
status: draft
last_review: "2026-02-13"
---

## Objective
Provide a **Value Realization** component for the 300s page that quantifies:
- **Potential Savings (EUR)**: what we expect to capture if the Action Code is executed successfully.
- **Realized Savings (EUR)**: what we actually captured, measured inside a defined success window.

This component is designed to prove the monetary value of analytics and create a closed governance loop from **data quality → KPI impact → action execution → realized value**.

## Inputs

### Metadata (registry output)
- `tooling/ontology/out/value_map.json`
  - `nodes.action_codes[*].impact_valuation`
  - `nodes.action_codes[*].tracking` (existing Action Code tracking block; outcome storage hints)
  - `impact_paths` (contract failure → KPI → UseCase → Action Codes)

### Fact tables (semantic layer)
The component assumes the ActionReady implementation logs into two facts (as already recommended in Action Codes):
- **Execution log**: `fact_action_execution`
  - Minimum columns: `ActionCode`, `TriggerLevel`, `ExecutedDate`, plus slice keys (Region/Channel/Product/…)
- **Outcome evaluation**: `fact_action_outcome`
  - Minimum columns: `ActionCode`, `AsOfDate`, and pre/post KPI values needed by `impact_valuation.calculation_logic`

## Core measures (Power BI / semantic model)

### 1) PotentialSavingsEUR
Definition: expected monetary value if success criteria are met in the success window.

Required metadata:
- `ActionCode.impact_valuation.method`
- `ActionCode.impact_valuation.currency`
- Optional: `impact.expected_range` and exposure measures (domain-specific)

Implementation note:
- Potential can be computed as **expected change × exposure × unit value**, where unit value is derived from governed KPIs (e.g., margin € per unit).
- Keep the formula deterministic and transparent; avoid black-box estimates.

### 2) RealizedSavingsEUR
Definition: realized monetary value measured after execution within the success window.

Uses:
- `impact_valuation.calculation_logic.standardized` as a **governance metadata contract** (not executed in code).
- Implement the actual DAX using logged pre/post metrics.

Examples:
- Direct margin improvement:
  - `RealizedEUR = Post_margin.gm.amount - Pre_margin.gm.amount`
- Cost avoidance:
  - `RealizedEUR = AvoidedCostEUR` (from outcome fact, or derived from KPI deltas)

### 3) SuccessFlag
Definition: 1 if success criteria met for the action in its success window.

Uses:
- `impact_valuation.success_window.duration`
- `impact_valuation.success_window.success_criteria`

### 4) SavingsGapEUR
Definition: `PotentialSavingsEUR - RealizedSavingsEUR`

## UI layout (300s page)

### Recommended visuals
- **Action Value Table** (by Action Code)
  - Columns: ActionCode, TriggerLevel, Executions (count), PotentialSavingsEUR, RealizedSavingsEUR, SavingsGapEUR, SuccessRate
- **Value Waterfall / Bar**
  - Potential vs Realized by ActionCode
- **Context panel**
  - Show success window, valuation method, and standardized formula string for auditability.

### Interaction model
- Filtered by Use Case (from `UseCase_Bracket`) and period.
- Drill-down by slices present in `fact_action_execution` (Region/Channel/Product…).

## Governance
- Never compute or mutate truth in the report layer without logging it in facts.
- Keep `impact_valuation.*` the single place defining how value is measured.
- Keep the registry output as metadata; computation happens in the semantic layer.

