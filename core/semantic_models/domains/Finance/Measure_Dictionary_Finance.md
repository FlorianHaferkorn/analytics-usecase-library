# Measure Dictionary - Finance

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
  kpi_id_ref: fin.cash.balance
  semantic_model: Finance_SemanticModel
  display_folder: 01_Liquidity
  category: KPI
  expression:
    aggregation_method: last_value
    logical: 'Cash Balance = SUM(fact_cash_position[Cash Balance Amount]) at MAX(DateKey) in filter context'
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
  kpi_id_ref: fin.cash.ocf
  semantic_model: Finance_SemanticModel
  display_folder: 01_Liquidity
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Cash generated from operating activities.
    notes: 'Grain: month. Unit: EUR.

      Lineage: fact_cashflow[OCF].

      QA: Align with cash flow statement; sign conventions consistent.

      '
  dependencies:
    columns:
    - fact_cashflow[OCF]
  governance:
    owner: Finance Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31
- measure_name: Cash vs Plan %
  is_kpi_measure: true
  kpi_id_ref: fin.cash.vs_plan.pct
  semantic_model: Finance_SemanticModel
  display_folder: 01_Liquidity
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
  kpi_id_ref: wc.ccc.days
  semantic_model: Finance_SemanticModel
  display_folder: 02_WorkingCapital
  category: KPI
  expression:
    aggregation_method: ratio
    logical: 'CCC = [DSO Days] + [DIO Days] - [DPO Days]'
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
  kpi_id_ref: wc.dso.days
  semantic_model: Finance_SemanticModel
  display_folder: 02_WorkingCapital
  category: KPI
  expression:
    aggregation_method: ratio
    logical: 'DSO = SUM(fact_ar[AR Amount]) / (SUM(fact_ar[Revenue Amount]) / 365)'
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
  kpi_id_ref: wc.dio.days
  semantic_model: Finance_SemanticModel
  display_folder: 02_WorkingCapital
  category: KPI
  expression:
    aggregation_method: ratio
    logical: 'DIO = SUM(fact_inventory[Inventory Amount]) / (SUM(fact_ap[COGS Amount]) / 365)'
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
  kpi_id_ref: wc.dpo.days
  semantic_model: Finance_SemanticModel
  display_folder: 02_WorkingCapital
  category: KPI
  expression:
    aggregation_method: ratio
    logical: 'DPO = SUM(fact_ap[AP Amount]) / (SUM(fact_ap[COGS Amount]) / 365)'
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
    logical: 'Fabric: see overlay / TMDL.'
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
    logical: 'Fabric: see overlay / TMDL.'
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
    logical: 'Fabric: see overlay / TMDL.'
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
    logical: 'Fabric: see overlay / TMDL.'
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
    logical: 'Fabric: see overlay / TMDL.'
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
    logical: 'Fabric: see overlay / TMDL.'
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
    logical: 'Fabric: see overlay / TMDL.'
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
    logical: 'Fabric: see overlay / TMDL.'
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
    logical: 'Fabric: see overlay / TMDL.'
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
    logical: 'Fabric: see overlay / TMDL.'
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
    logical: 'Fabric: see overlay / TMDL.'
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
  kpi_id_ref: cost.unit.amount
  semantic_model: Finance_SemanticModel
  display_folder: 03_Cost
  category: KPI
  expression:
    aggregation_method: ratio
    logical: 'Unit Cost = SUM(fact_cost[COGS Amount]) / SUM(fact_output[Output Units])'
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
  kpi_id_ref: margin.cogs.pct
  semantic_model: Finance_SemanticModel
  display_folder: 03_Cost
  category: KPI
  expression:
    aggregation_method: ratio
    logical: 'COGS % = SUM(fact_finance[COGS Amount]) / SUM(fact_finance[Net Sales Amount])'
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
  kpi_id_ref: cost.opex.vs_plan.pct
  semantic_model: Finance_SemanticModel
  display_folder: 04_OpEx
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
  kpi_id_ref: cost.material.pct
  semantic_model: Finance_SemanticModel
  display_folder: 03_Cost
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
  kpi_id_ref: ops.labor.productivity.pct
  semantic_model: Finance_SemanticModel
  display_folder: 05_Productivity
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Finance_SemanticModel
  display_folder: 06_Profitability
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: EBITDA / Net Sales.
    notes: 'Grain: month. Unit: %.

      Lineage: fact_finance[EBITDA], fact_finance[Net Sales].

      QA: Net Sales > 0; EBITDA definition aligned to P&L.

      '
  dependencies:
    columns:
    - fact_finance[EBITDA]
    - fact_finance[Net Sales]
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
    logical: 'Fabric: see overlay / TMDL.'
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
```

