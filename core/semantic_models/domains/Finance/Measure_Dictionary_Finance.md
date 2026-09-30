# Measure Dictionary - Finance

> **Generated view.** The source of truth is the per-measure files under [`measures/`](measures/). Edit those (or use ActionReady Studio); regenerate this file with `python tooling/codegen/measure_dictionary_files.py render`.

Schema: see `core/semantic_models/Domain_Measure_Dictionary_Schema.md`

## Aggregation Method Conventions

All measures must declare an `aggregation_method` in their `expression` block. Conventions:

| Method | Use for |
|--------|---------|
| `sum` | Additive facts (amounts, units, hours) — safe to aggregate across all dimensions |
| `average` | Rate-based or averaged measures (headcount, pricing averages) — dimension-sensitive |
| `last_value` | Stock/balance measures (cash position, AR balance, inventory) — not additive across time |
| `ratio` | Calculated ratios (%, days) — must be computed from component measures, not averaged |
| `count` | Event counts — additive |

**Rule:** Ratio measures (`%`, `days`) must never be averaged directly. Always re-compute from summed numerator/denominator components when changing filter context.

## Logical Expression Convention

`expression.logical` contains a tool-agnostic business-logic pseudocode. This is the single source of truth for what the measure calculates. Tool-specific implementation (DAX, SQL, Python) lives in the adapter layer (`products/fabric/`).

Format: `MEASURE_NAME = <pseudocode using column references from data contract>`

```yaml
- measure_name: Cash Balance
  is_kpi_measure: true
  kpi_id_ref: KPI-FIN-007
  semantic_model: Finance_SemanticModel
  display_folder: 01_Liquidity
  category: KPI
  expression:
    aggregation_method: last_value
    logical: Cash Balance = SUM(fact_cash_position[Cash Balance Amount]) at MAX(DateKey) in filter context
  documentation:
    description: Cash and cash equivalents.
    notes: 'Grain: day. Unit: EUR.

      Lineage: fact_cash[Cash Balance].

      QA: Reconcile to GL; currency conversion upstream.

      '
  dependencies:
    columns:
    - fact_cash[Cash Balance]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Operating Cash Flow
  is_kpi_measure: true
  kpi_id_ref: KPI-FIN-009
  category: KPI
  expression:
    aggregation_method: sum
    logical: Operating Cash Flow = SUM(fact_cashflow[Operating Cash Flow Amount]) for the reporting period
  governance:
    status: active
    owner: Finance Analytics
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31
  dependencies:
    columns:
    - fact_cashflow[Operating Cash Flow Amount]
  semantic_model: Finance_SemanticModel
  display_folder: 01_Liquidity
  documentation:
    description: Cash generated from operating activities.
    notes: 'Grain: month. Unit: EUR.

      Lineage: fact_cashflow[OCF].

      QA: Align with cash flow statement; sign conventions consistent.

      '

- measure_name: Cash vs Plan %
  is_kpi_measure: true
  kpi_id_ref: KPI-FIN-010
  semantic_model: Finance_SemanticModel
  display_folder: 01_Liquidity
  category: KPI
  expression:
    logical: Cash vs Plan % = (Cash Balance - Cash Plan) / Cash Plan.
    aggregation_method: ratio
  documentation:
    description: Performance vs plan for cash position.
    notes: 'Grain: month. Unit: %.

      Lineage: [Cash Balance], plan_cash.

      QA: DIVIDE guard; plan completeness required.

      '
  dependencies:
    measures:
    - '[Cash Balance]'
    columns:
    - plan_cash[Cash Balance]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: CCC Days
  is_kpi_measure: true
  kpi_id_ref: KPI-FIN-006
  semantic_model: Finance_SemanticModel
  display_folder: 02_WorkingCapital
  category: KPI
  expression:
    aggregation_method: ratio
    logical: CCC = [DSO Days] + [DIO Days] - [DPO Days]
  documentation:
    description: Working capital cycle time.
    notes: 'Grain: month. Unit: days.

      Lineage: DSO, DIO, DPO measures.

      QA: Ensure consistent revenue/COGS bases across components.

      '
  dependencies:
    measures:
    - '[DSO (days)]'
    - '[DIO (days)]'
    - '[DPO (days)]'
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: DSO Days
  is_kpi_measure: true
  kpi_id_ref: KPI-FIN-001
  semantic_model: Finance_SemanticModel
  display_folder: 02_WorkingCapital
  category: KPI
  expression:
    aggregation_method: ratio
    logical: DSO = SUM(fact_ar[AR Amount]) / (SUM(fact_ar[Revenue Amount]) / 365)
  documentation:
    description: 'Receivables efficiency: AR / (Revenue/365).'
    notes: 'Grain: month. Unit: days.

      Lineage: fact_ar[AR], revenue.

      QA: Revenue basis aligns to AR window; currency consistency.

      '
  dependencies:
    columns:
    - fact_ar[AR]
    - fact_sales[Net Sales Amount]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: DIO Days
  is_kpi_measure: true
  kpi_id_ref: KPI-FIN-004
  semantic_model: Finance_SemanticModel
  display_folder: 02_WorkingCapital
  category: KPI
  expression:
    aggregation_method: ratio
    logical: DIO = SUM(fact_inventory[Inventory Amount]) / (SUM(fact_ap[COGS Amount]) / 365)
  documentation:
    description: 'Inventory efficiency: Inventory / (COGS/365).'
    notes: 'Grain: month. Unit: days.

      Lineage: fact_inventory[Inventory], fact_cogs[COGS].

      QA: Inventory valuation consistent; COGS aligned to period.

      '
  dependencies:
    columns:
    - fact_inventory[Inventory]
    - fact_cogs[COGS]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: DPO Days
  is_kpi_measure: true
  kpi_id_ref: KPI-FIN-005
  semantic_model: Finance_SemanticModel
  display_folder: 02_WorkingCapital
  category: KPI
  expression:
    aggregation_method: ratio
    logical: DPO = SUM(fact_ap[AP Amount]) / (SUM(fact_ap[COGS Amount]) / 365)
  documentation:
    description: 'Payables efficiency: AP / (COGS/365).'
    notes: 'Grain: month. Unit: days.

      Lineage: fact_ap[AP], fact_cogs[COGS].

      QA: COGS alignment; AP completeness.

      '
  dependencies:
    columns:
    - fact_ap[AP]
    - fact_cogs[COGS]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: AR Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Finance_SemanticModel
  display_folder: 02_WorkingCapital
  category: Base
  expression:
    logical: AR Amount = SUM(fact_ar[AR Amount])
    aggregation_method: sum
  documentation:
    description: Accounts receivable balance for DSO calculations.
    notes: 'Source: fact_ar. Aligns to revenue period.'
  dependencies:
    columns:
    - fact_ar[AR Amount]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Revenue Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Finance_SemanticModel
  display_folder: 02_WorkingCapital
  category: Base
  expression:
    logical: Revenue Amount = SUM(fact_ar[Revenue Amount])
    aggregation_method: sum
  documentation:
    description: Revenue base used in DSO calculations.
    notes: 'Source: fact_ar.'
  dependencies:
    columns:
    - fact_ar[Revenue Amount]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: AP Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Finance_SemanticModel
  display_folder: 02_WorkingCapital
  category: Base
  expression:
    logical: AP Amount = SUM(fact_ap[AP Amount])
    aggregation_method: sum
  documentation:
    description: Accounts payable balance for DPO calculations.
    notes: 'Source: fact_ap.'
  dependencies:
    columns:
    - fact_ap[AP Amount]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Inventory Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Finance_SemanticModel
  display_folder: 02_WorkingCapital
  category: Base
  expression:
    logical: Inventory Amount = SUM(fact_inventory[Inventory Amount])
    aggregation_method: sum
  documentation:
    description: Inventory balance used in DIO calculations.
    notes: 'Source: fact_inventory.'
  dependencies:
    columns:
    - fact_inventory[Inventory Amount]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Net Sales Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Finance_SemanticModel
  display_folder: 03_Cost
  category: Base
  expression:
    logical: Net Sales Amount = SUM ( fact_sales[Net Sales Amount] )
    aggregation_method: sum
  documentation:
    description: Net sales base for cost ratios.
    notes: 'Source: fact_finance.'
  dependencies:
    columns:
    - fact_finance[Net Sales Amount]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: COGS Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Finance_SemanticModel
  display_folder: 03_Cost
  category: Base
  expression:
    logical: COGS Amount = SUM(fact_finance[COGS Amount])
    aggregation_method: sum
  documentation:
    description: Cost of goods sold base for cost ratios.
    notes: 'Source: fact_finance.'
  dependencies:
    columns:
    - fact_finance[COGS Amount]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Material Cost Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Finance_SemanticModel
  display_folder: 03_Cost
  category: Base
  expression:
    logical: Material Cost Amount = SUM(fact_finance[Material Cost Amount])
    aggregation_method: sum
  documentation:
    description: Material cost base for material share calculations.
    notes: 'Source: fact_finance.'
  dependencies:
    columns:
    - fact_finance[Material Cost Amount]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: OpEx Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Finance_SemanticModel
  display_folder: 04_OpEx
  category: Base
  expression:
    logical: OpEx Amount = SUM(fact_finance[OpEx Amount])
    aggregation_method: sum
  documentation:
    description: Operating expenses base.
    notes: 'Source: fact_finance.'
  dependencies:
    columns:
    - fact_finance[OpEx Amount]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Plan OpEx Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Finance_SemanticModel
  display_folder: 04_OpEx
  category: Base
  expression:
    logical: Plan OpEx Amount = SUM(fact_finance[Plan OpEx Amount])
    aggregation_method: sum
  documentation:
    description: Planned operating expenses base.
    notes: 'Source: fact_finance.'
  dependencies:
    columns:
    - fact_finance[Plan OpEx Amount]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Output Units
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Finance_SemanticModel
  display_folder: 05_Productivity
  category: Base
  expression:
    logical: Output Units = SUM(fact_output[Output Units])
    aggregation_method: sum
  documentation:
    description: Output units for productivity and unit cost metrics.
    notes: 'Source: fact_output.'
  dependencies:
    columns:
    - fact_output[Output Units]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Labor Hours
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Finance_SemanticModel
  display_folder: 05_Productivity
  category: Base
  expression:
    logical: Labor Hours = SUM(fact_labor[Labor Hours])
    aggregation_method: sum
  documentation:
    description: Labor hours for productivity calculations.
    notes: 'Source: fact_labor.'
  dependencies:
    columns:
    - fact_labor[Labor Hours]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Unit Cost Amount
  is_kpi_measure: true
  kpi_id_ref: KPI-FIN-015
  semantic_model: Finance_SemanticModel
  display_folder: 03_Cost
  category: KPI
  expression:
    aggregation_method: ratio
    logical: Unit Cost = SUM(fact_cost[COGS Amount]) / SUM(fact_output[Output Units])
  documentation:
    description: Total COGS / units produced or sold.
    notes: 'Grain: plant_line_product_month. Unit: EUR per unit.

      Lineage: fact_cost[COGS], fact_output[Units].

      QA: Units > 0; consistent cost allocation.

      '
  dependencies:
    columns:
    - fact_cost[COGS]
    - fact_output[Units]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: COGS % of Sales
  is_kpi_measure: true
  kpi_id_ref: KPI-FIN-016
  semantic_model: Finance_SemanticModel
  display_folder: 03_Cost
  category: KPI
  expression:
    aggregation_method: ratio
    logical: COGS % = SUM(fact_finance[COGS Amount]) / SUM(fact_finance[Net Sales Amount])
  documentation:
    description: 'Cost share: COGS / Net Sales.'
    notes: 'Grain: month. Unit: %.

      Lineage: fact_finance[COGS], fact_finance[Net Sales].

      QA: Net Sales > 0; currency alignment.

      '
  dependencies:
    columns:
    - fact_finance[COGS]
    - fact_finance[Net Sales]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: OpEx vs Plan %
  is_kpi_measure: true
  kpi_id_ref: KPI-FIN-014
  semantic_model: Finance_SemanticModel
  display_folder: 04_OpEx
  category: KPI
  expression:
    logical: OpEx vs Plan % = (OpEx Amount - OpEx Plan Amount) / OpEx Plan Amount.
    aggregation_method: ratio
  documentation:
    description: 'Overhead control: (OpEx - Plan) / Plan.'
    notes: 'Grain: month. Unit: %.

      Lineage: fact_opex[OpEx], plan_opex.

      QA: Plan available; sign conventions consistent.

      '
  dependencies:
    columns:
    - fact_opex[OpEx]
    - plan_opex[Plan OpEx]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Material Cost %
  is_kpi_measure: true
  kpi_id_ref: KPI-SCM-020
  semantic_model: Finance_SemanticModel
  display_folder: 03_Cost
  category: KPI
  expression:
    logical: Material Cost % = Material Cost Amount / Net Sales Amount.
    aggregation_method: ratio
  documentation:
    description: Material cost / Net Sales.
    notes: 'Grain: month. Unit: %.

      Lineage: fact_cost[Material Cost], fact_finance[Net Sales].

      QA: Net Sales > 0; material cost completeness.

      '
  dependencies:
    columns:
    - fact_cost[Material Cost]
    - fact_finance[Net Sales]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Labor Productivity %
  is_kpi_measure: true
  kpi_id_ref: KPI-OPS-004
  semantic_model: Finance_SemanticModel
  display_folder: 05_Productivity
  category: KPI
  expression:
    logical: Labor Productivity % = Output Units or Net Sales divided by Labor Hours (normalized to % baseline).
    aggregation_method: ratio
  documentation:
    description: Output vs labor hours (or revenue per labor hour).
    notes: 'Grain: month. Unit: % / index.

      Lineage: fact_output[Units], fact_labor[Labor Hours].

      QA: Hours > 0; consistent time tracking.

      '
  dependencies:
    columns:
    - fact_output[Units]
    - fact_labor[Labor Hours]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: EBITDA Margin
  is_kpi_measure: true
  kpi_id_ref: KPI-FIN-018
  semantic_model: Finance_SemanticModel
  display_folder: 06_Profitability
  category: KPI
  expression:
    logical: EBITDA Margin = DIVIDE ( SUM ( fact_finance[EBITDA Amount] ), SUM ( fact_finance[Net Sales Amount] ) )
    aggregation_method: ratio
  documentation:
    description: EBITDA / Net Sales.
    notes: 'Grain: month. Unit: %.

      Lineage: fact_finance[EBITDA], fact_finance[Net Sales].

      QA: Net Sales > 0; EBITDA definition aligned to P&L.

      '
  dependencies:
    columns:
    - fact_finance[EBITDA Amount]
    - fact_finance[Net Sales Amount]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: COGS Amount (AP)
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Finance_SemanticModel
  display_folder: 02_WorkingCapital
  category: Base
  expression:
    logical: COGS Amount (AP) = SUM(fact_ap[COGS Amount])
    aggregation_method: sum
  documentation:
    description: COGS amount used as AP base for DPO calculations.
    notes: 'Source: fact_ap[COGS Amount].'
  dependencies:
    columns:
    - fact_ap[COGS Amount]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Net Sales Amount (FIN)
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Finance_SemanticModel
  display_folder: 03_Cost
  category: Base
  expression:
    logical: Net Sales Amount (FIN) = SUM ( fact_sales[Net Sales Amount] )
    aggregation_method: sum
  documentation:
    description: Total invoiced revenue net of discounts and returns, Finance domain view.
    notes: 'Grain: invoice_line, reported monthly. Unit: EUR. Lineage: fact_sales[Net Sales Amount].'
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 28.04.2026

- measure_name: OTIF % (FIN)
  is_kpi_measure: true
  kpi_id_ref: KPI-SCM-007
  semantic_model: Finance_SemanticModel
  display_folder: FIN-001
  category: KPI
  expression:
    logical: OTIF % (FIN) = VAR OTIFFulfillments = CALCULATE ( COUNTROWS ( fact_fulfillment ), fact_fulfillment[OTIF Flag] = TRUE() ) VAR TotalFulfillments = COUNTROWS ( fact_fulfillment ) RETURN DIVIDE ( OTIFFulfillments, TotalFulfillments )
    aggregation_method: custom
  documentation:
    description: Measures share of orders delivered on time and in full — governed OTIF, Finance cross-domain view (consolidated from the former Supply Chain / Operations Service Level %).
    notes: 'Grain: order_line_day. Unit: %. Lineage: fact_fulfillment[OTIF Flag].'
  dependencies:
    columns:
    - fact_fulfillment[OTIF Flag]
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 2026-07-17

- measure_name: Throughput Units (FIN)
  is_kpi_measure: true
  kpi_id_ref: KPI-OPS-009
  semantic_model: Finance_SemanticModel
  display_folder: FIN-002
  category: KPI
  expression:
    logical: Throughput Units (FIN) = SUM ( fact_output[Output Units] )
    aggregation_method: sum
  documentation:
    description: Total produced units in the period — governed throughput, Finance cross-domain view (consolidated from the former Production Volume Units).
    notes: 'Grain: line_day. Unit: units. Lineage: fact_output[Output Units].'
  dependencies:
    columns:
    - fact_output[Output Units]
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 2026-07-17

- measure_name: Quality % (FIN)
  is_kpi_measure: true
  kpi_id_ref: KPI-OPS-003
  semantic_model: Finance_SemanticModel
  display_folder: FIN-002
  category: KPI
  expression:
    logical: Quality % (FIN) = VAR GoodUnits = SUM ( fact_ops[Good Units] ) VAR TotalUnits = SUM ( fact_ops[Output Units] ) RETURN DIVIDE ( GoodUnits, TotalUnits )
    aggregation_method: custom
  documentation:
    description: Good units divided by total output — governed quality/yield, Finance cross-domain view (consolidated from the former Yield %).
    notes: 'Grain: line_day. Unit: %. Lineage: fact_ops[Good Units], fact_ops[Output Units]. Known pre-existing data gap — the Finance model carries fact_output[Output Units] but no Good-Units source, so this proxy cannot evaluate in the Finance model until Good Units is added.'
  dependencies:
    columns:
    - fact_ops[Good Units]
    - fact_ops[Output Units]
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 2026-07-17

- measure_name: Actions Executed Count (XD)
  is_kpi_measure: true
  kpi_id_ref: KPI-GOV-005
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Actions Executed Count (XD) = COUNTROWS ( FILTER ( fact_action_outcome, NOT ISBLANK ( fact_action_outcome[outcome_status] ) ) )
    aggregation_method: count
  documentation:
    notes: 'Grain: month. Unit: count. Lineage: fact_action_outcome[outcome_status].'
    description: Number of action codes with a recorded outcome — Finance domain cross-domain view.
  dependencies:
    columns:
    - fact_action_outcome[outcome_status]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Finance BI
  semantic_model: Finance_SemanticModel

- measure_name: Action Outcome Rate % (XD)
  is_kpi_measure: true
  kpi_id_ref: KPI-GOV-001
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Action Outcome Rate % (XD) = DIVIDE ( CALCULATE ( COUNTROWS ( fact_action_outcome ), fact_action_outcome[outcome_status] = "achieved" ), COUNTROWS ( fact_action_outcome ) )
    aggregation_method: custom
  documentation:
    notes: 'Grain: month. Unit: %. Lineage: fact_action_outcome[outcome_status].'
    description: Percentage of executed actions with a confirmed achieved outcome — Finance domain cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[outcome_status]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Finance BI
  semantic_model: Finance_SemanticModel

- measure_name: Avg Time-to-Outcome Days (XD)
  is_kpi_measure: true
  kpi_id_ref: KPI-GOV-006
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Avg Time-to-Outcome Days (XD) = AVERAGEX ( fact_action_outcome, fact_action_outcome[days_to_outcome] )
    aggregation_method: average
  documentation:
    notes: 'Grain: month. Unit: days. Lineage: fact_action_outcome[days_to_outcome].'
    description: Average days between action execution and outcome confirmation — Finance domain cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[days_to_outcome]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Finance BI
  semantic_model: Finance_SemanticModel

- measure_name: Action ROI % (XD)
  is_kpi_measure: true
  kpi_id_ref: KPI-GOV-007
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Action ROI % (XD) = DIVIDE ( SUMX ( fact_action_outcome, fact_action_outcome[impact_value] ), SUMX ( fact_action_outcome, fact_action_outcome[cost_to_execute] ) ) - 1
    aggregation_method: custom
  documentation:
    notes: 'Grain: month. Unit: %. Lineage: fact_action_outcome[impact_value], fact_action_outcome[cost_to_execute].'
    description: Average ROI of executed actions — Finance domain cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[impact_value]
    - fact_action_outcome[cost_to_execute]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Finance BI
  semantic_model: Finance_SemanticModel

- measure_name: Action Effectiveness Delta (XD)
  is_kpi_measure: true
  kpi_id_ref: KPI-GOV-002
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Action Effectiveness Delta (XD) = AVERAGEX ( FILTER ( fact_action_outcome, fact_action_outcome[outcome_status] = "achieved" ), fact_action_outcome[impact_value] )
    aggregation_method: average
  documentation:
    notes: 'Grain: month. Unit: EUR. Lineage: fact_action_outcome[impact_value], fact_action_outcome[outcome_status].'
    description: Average EUR impact per achieved action execution — Finance domain cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[impact_value]
    - fact_action_outcome[outcome_status]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Finance BI
  semantic_model: Finance_SemanticModel
```

