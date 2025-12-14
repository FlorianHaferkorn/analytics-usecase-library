# Measure Dictionary - Finance

Schema: see `/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: "Cash Balance"
  is_kpi_measure: true
  kpi_id_ref: "fin.cash.balance"
  semantic_model: "Finance_SemanticModel"
  display_folder: "01_Liquidity"
  category: "KPI"
  expression:
    dax: "SUM(fact_cash[Cash Balance])"
    formatString: "EUR #,0"
  documentation:
    description: "Cash and cash equivalents."
    notes: |
      Grain: day. Unit: EUR.
      Lineage: fact_cash[Cash Balance].
      QA: Reconcile to GL; currency conversion upstream.
  dependencies:
    columns:
      - "fact_cash[Cash Balance]"
  governance:
    owner: "Finance Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Operating Cash Flow"
  is_kpi_measure: true
  kpi_id_ref: "fin.cash.ocf"
  semantic_model: "Finance_SemanticModel"
  display_folder: "01_Liquidity"
  category: "KPI"
  expression:
    dax: "SUM(fact_cashflow[OCF])"
    formatString: "EUR #,0"
  documentation:
    description: "Cash generated from operating activities."
    notes: |
      Grain: month. Unit: EUR.
      Lineage: fact_cashflow[OCF].
      QA: Align with cash flow statement; sign conventions consistent.
  dependencies:
    columns:
      - "fact_cashflow[OCF]"
  governance:
    owner: "Finance Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Cash vs Plan %"
  is_kpi_measure: true
  kpi_id_ref: "fin.cash.vs_plan.pct"
  semantic_model: "Finance_SemanticModel"
  display_folder: "01_Liquidity"
  category: "KPI"
  expression:
    dax: |
      VAR PlanCash = SUM ( plan_cash[Cash Balance] )
      RETURN DIVIDE ( [Cash Balance] - PlanCash, PlanCash )
    formatString: "0.0%"
  documentation:
    description: "Performance vs plan for cash position."
    notes: |
      Grain: month. Unit: %.
      Lineage: [Cash Balance], plan_cash.
      QA: DIVIDE guard; plan completeness required.
  dependencies:
    measures:
      - "[Cash Balance]"
    columns:
      - "plan_cash[Cash Balance]"
  governance:
    owner: "Finance Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Cash Conversion Cycle (days)"
  is_kpi_measure: true
  kpi_id_ref: "wc.ccc.days"
  semantic_model: "Finance_SemanticModel"
  display_folder: "02_WorkingCapital"
  category: "KPI"
  expression:
    dax: "[DSO (days)] + [DIO (days)] - [DPO (days)]"
    formatString: "0"
  documentation:
    description: "Working capital cycle time."
    notes: |
      Grain: month. Unit: days.
      Lineage: DSO, DIO, DPO measures.
      QA: Ensure consistent revenue/COGS bases across components.
  dependencies:
    measures:
      - "[DSO (days)]"
      - "[DIO (days)]"
      - "[DPO (days)]"
  governance:
    owner: "Finance Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "DSO (days)"
  is_kpi_measure: true
  kpi_id_ref: "wc.dso.days"
  semantic_model: "Finance_SemanticModel"
  display_folder: "02_WorkingCapital"
  category: "KPI"
  expression:
    dax: |
      VAR AR      = SUM ( fact_ar[AR] )
      VAR Revenue = SUM ( fact_sales[Net Sales Amount] )
      VAR RevenuePerDay = DIVIDE ( Revenue, 365 )
      RETURN DIVIDE ( AR, RevenuePerDay )
    formatString: "0"
  documentation:
    description: "Receivables efficiency: AR / (Revenue/365)."
    notes: |
      Grain: month. Unit: days.
      Lineage: fact_ar[AR], revenue.
      QA: Revenue basis aligns to AR window; currency consistency.
  dependencies:
    columns:
      - "fact_ar[AR]"
      - "fact_sales[Net Sales Amount]"
  governance:
    owner: "Finance Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "DIO (days)"
  is_kpi_measure: true
  kpi_id_ref: "wc.dio.days"
  semantic_model: "Finance_SemanticModel"
  display_folder: "02_WorkingCapital"
  category: "KPI"
  expression:
    dax: |
      VAR Inv       = SUM ( fact_inventory[Inventory] )
      VAR Cogs      = SUM ( fact_cogs[COGS] )
      VAR CogsPerDay = DIVIDE ( Cogs, 365 )
      RETURN DIVIDE ( Inv, CogsPerDay )
    formatString: "0"
  documentation:
    description: "Inventory efficiency: Inventory / (COGS/365)."
    notes: |
      Grain: month. Unit: days.
      Lineage: fact_inventory[Inventory], fact_cogs[COGS].
      QA: Inventory valuation consistent; COGS aligned to period.
  dependencies:
    columns:
      - "fact_inventory[Inventory]"
      - "fact_cogs[COGS]"
  governance:
    owner: "Finance Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "DPO (days)"
  is_kpi_measure: true
  kpi_id_ref: "wc.dpo.days"
  semantic_model: "Finance_SemanticModel"
  display_folder: "02_WorkingCapital"
  category: "KPI"
  expression:
    dax: |
      VAR AP       = SUM ( fact_ap[AP] )
      VAR Cogs     = SUM ( fact_cogs[COGS] )
      VAR CogsPerDay = DIVIDE ( Cogs, 365 )
      RETURN DIVIDE ( AP, CogsPerDay )
    formatString: "0"
  documentation:
    description: "Payables efficiency: AP / (COGS/365)."
    notes: |
      Grain: month. Unit: days.
      Lineage: fact_ap[AP], fact_cogs[COGS].
      QA: COGS alignment; AP completeness.
  dependencies:
    columns:
      - "fact_ap[AP]"
      - "fact_cogs[COGS]"
  governance:
    owner: "Finance Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Unit Cost Amount"
  is_kpi_measure: true
  kpi_id_ref: "cost.unit.amount"
  semantic_model: "Finance_SemanticModel"
  display_folder: "03_Cost"
  category: "KPI"
  expression:
    dax: |
      VAR Cogs  = SUM ( fact_cost[COGS] )
      VAR Units = SUM ( fact_output[Units] )
      RETURN DIVIDE ( Cogs, Units )
    formatString: "EUR per unit"
  documentation:
    description: "Total COGS / units produced or sold."
    notes: |
      Grain: plant_line_product_month. Unit: EUR per unit.
      Lineage: fact_cost[COGS], fact_output[Units].
      QA: Units > 0; consistent cost allocation.
  dependencies:
    columns:
      - "fact_cost[COGS]"
      - "fact_output[Units]"
  governance:
    owner: "Finance Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "COGS % of Sales"
  is_kpi_measure: true
  kpi_id_ref: "margin.cogs.pct"
  semantic_model: "Finance_SemanticModel"
  display_folder: "03_Cost"
  category: "KPI"
  expression:
    dax: |
      VAR Cogs      = SUM ( fact_finance[COGS] )
      VAR NetSales  = SUM ( fact_finance[Net Sales] )
      RETURN DIVIDE ( Cogs, NetSales )
    formatString: "0.0%"
  documentation:
    description: "Cost share: COGS / Net Sales."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_finance[COGS], fact_finance[Net Sales].
      QA: Net Sales > 0; currency alignment.
  dependencies:
    columns:
      - "fact_finance[COGS]"
      - "fact_finance[Net Sales]"
  governance:
    owner: "Finance Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "OpEx vs Plan %"
  is_kpi_measure: true
  kpi_id_ref: "cost.opex.vs_plan.pct"
  semantic_model: "Finance_SemanticModel"
  display_folder: "04_OpEx"
  category: "KPI"
  expression:
    dax: |
      VAR OpExPlan = SUM ( plan_opex[Plan OpEx] )
      VAR OpExAct  = SUM ( fact_opex[OpEx] )
      RETURN DIVIDE ( OpExAct - OpExPlan, OpExPlan )
    formatString: "0.0%"
  documentation:
    description: "Overhead control: (OpEx - Plan) / Plan."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_opex[OpEx], plan_opex.
      QA: Plan available; sign conventions consistent.
  dependencies:
    columns:
      - "fact_opex[OpEx]"
      - "plan_opex[Plan OpEx]"
  governance:
    owner: "Finance Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Material Cost %"
  is_kpi_measure: true
  kpi_id_ref: "cost.material.pct"
  semantic_model: "Finance_SemanticModel"
  display_folder: "03_Cost"
  category: "KPI"
  expression:
    dax: |
      VAR MatCost = SUM ( fact_cost[Material Cost] )
      VAR NetSales = SUM ( fact_finance[Net Sales] )
      RETURN DIVIDE ( MatCost, NetSales )
    formatString: "0.0%"
  documentation:
    description: "Material cost / Net Sales."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_cost[Material Cost], fact_finance[Net Sales].
      QA: Net Sales > 0; material cost completeness.
  dependencies:
    columns:
      - "fact_cost[Material Cost]"
      - "fact_finance[Net Sales]"
  governance:
    owner: "Finance Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Labor Productivity %"
  is_kpi_measure: true
  kpi_id_ref: "ops.labor.productivity.pct"
  semantic_model: "Finance_SemanticModel"
  display_folder: "05_Productivity"
  category: "KPI"
  expression:
    dax: |
      VAR Output = SUM ( fact_output[Units] )
      VAR Hours  = SUM ( fact_labor[Labor Hours] )
      RETURN DIVIDE ( Output, Hours )
    formatString: "0.0%"
  documentation:
    description: "Output vs labor hours (or revenue per labor hour)."
    notes: |
      Grain: month. Unit: % / index.
      Lineage: fact_output[Units], fact_labor[Labor Hours].
      QA: Hours > 0; consistent time tracking.
  dependencies:
    columns:
      - "fact_output[Units]"
      - "fact_labor[Labor Hours]"
  governance:
    owner: "Finance Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "EBITDA Margin"
  is_kpi_measure: true
  kpi_id_ref: "profit.ebitda_margin"
  semantic_model: "Finance_SemanticModel"
  display_folder: "06_Profitability"
  category: "KPI"
  expression:
    dax: |
      VAR Ebitda   = SUM ( fact_finance[EBITDA] )
      VAR NetSales = SUM ( fact_finance[Net Sales] )
      RETURN DIVIDE ( Ebitda, NetSales )
    formatString: "0.0%"
  documentation:
    description: "EBITDA / Net Sales."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_finance[EBITDA], fact_finance[Net Sales].
      QA: Net Sales > 0; EBITDA definition aligned to P&L.
  dependencies:
    columns:
      - "fact_finance[EBITDA]"
      - "fact_finance[Net Sales]"
  governance:
    owner: "Finance Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
```
