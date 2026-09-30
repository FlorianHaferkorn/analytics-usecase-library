# Measure Dictionary - CustomerValue

> **Generated view.** The source of truth is the per-measure files under [`measures/`](measures/). Edit those (or use ActionReady Studio); regenerate this file with `python tooling/codegen/measure_dictionary_files.py render`.

Schema: see `core/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Net Sales Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: CustomerValue_SemanticModel
  display_folder: 00_Base
  category: Base
  expression:
    logical: Net Sales Amount = SUM ( fact_sales[Net Sales Amount] )
    aggregation_method: sum
  documentation:
    description: Base measure summing net sales for all transactions.
    notes: Excludes VAT/returns; currency conversion handled upstream.
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
  governance:
    owner: CRM BI
    status: active
    version: v1.2
    last_review: 12.12.2025

- measure_name: Customer Lifetime Value Amount
  is_kpi_measure: true
  kpi_id_ref: KPI-CUS-001
  semantic_model: CustomerValue_SemanticModel
  display_folder: 04_Customer
  category: KPI
  expression:
    logical: Customer Lifetime Value Amount = Sum of expected future gross margin per customer discounted over the chosen time horizon.
    aggregation_method: sum
  documentation:
    description: Discounted lifetime value per customer sourced from the CLV mart.
    notes: CLV methodology (horizon, discount rate) defined upstream.
  dependencies:
    columns:
    - fact_customer_value[CLV Amount]
  governance:
    owner: CRM BI
    status: active
    version: v1.2
    last_review: 12.12.2025

- measure_name: Customer Lifetime Revenue Amount
  is_kpi_measure: true
  kpi_id_ref: KPI-CUS-005
  semantic_model: CustomerValue_SemanticModel
  display_folder: 01_Revenue
  category: KPI
  expression:
    logical: Customer Lifetime Revenue Amount = Sum of net sales amount from first purchase to date for the customer.
    aggregation_method: sum
  documentation:
    description: Total realised revenue per customer across lifecycle; resets date context to accumulate.
    notes: Uses Net Sales Amount as base; lifecycle completeness handled upstream.
  dependencies:
    measures:
    - Net Sales Amount
    columns:
    - dim_customer[CustomerKey]
  governance:
    owner: CRM BI
    status: active
    version: v1.2
    last_review: 12.12.2025

- measure_name: Active Customers Count
  is_kpi_measure: true
  kpi_id_ref: KPI-CUS-006
  semantic_model: CustomerValue_SemanticModel
  display_folder: 01_Retention
  category: KPI
  expression:
    logical: Active Customers Count = Distinct customers with at least one qualifying transaction in the period.
    aggregation_method: count
  documentation:
    description: Active customers in the period based on activity flag.
    notes: Forms the base for retention/churn metrics.
  dependencies:
    columns:
    - dim_customer[CustomerKey]
    - fact_customer_events[Activity Flag]
  governance:
    owner: CRM BI
    status: active
    version: v1.2
    last_review: 12.12.2025

- measure_name: Churned Customers Count
  is_kpi_measure: true
  kpi_id_ref: KPI-CUS-004
  semantic_model: CustomerValue_SemanticModel
  display_folder: 01_Retention
  category: KPI
  expression:
    logical: Churned Customers Count = Distinct customers with no qualifying transactions in the current period but active in the look-back window.
    aggregation_method: count
  documentation:
    description: Customers flagged as churned in the selected period.
    notes: Depends on churn flag in fact_customer_events.
  dependencies:
    columns:
    - dim_customer[CustomerKey]
    - fact_customer_events[Churn Flag]
  governance:
    owner: CRM BI
    status: active
    version: v1.2
    last_review: 12.12.2025

- measure_name: Customer Retention %
  is_kpi_measure: true
  kpi_id_ref: KPI-CUS-002
  semantic_model: CustomerValue_SemanticModel
  display_folder: 01_Retention
  category: KPI
  expression:
    logical: Customer Retention % = (Active Customers at end of period) / (Active Customers at start of period).
    aggregation_method: ratio
  documentation:
    description: Retained customers as share of opening active base in the period.
    notes: Relies on activity/churn flags in fact_customer_events.
  dependencies:
    measures:
    - Active Customers Count
    - Churned Customers Count
  governance:
    owner: CRM BI
    status: active
    version: v1.2
    last_review: 12.12.2025

- measure_name: Revenue at Risk Amount
  is_kpi_measure: true
  kpi_id_ref: KPI-OPS-001
  semantic_model: CustomerValue_SemanticModel
  display_folder: 01_Retention
  category: KPI
  expression:
    logical: Revenue at Risk Amount = CLV Remaining Amount * Attrition Risk %.
    aggregation_method: sum
  documentation:
    description: Exposure sizing from churn-risk customers based on CLV remaining and attrition risk.
    notes: Attrition Risk % delivered as 0�100 is auto-scaled to 0�1. CLV and Remaining follow finance-approved discount rate and CLV horizon (use finance WACC and agreed horizon).
  dependencies:
    columns:
    - fact_customer_value[CLV Remaining Amount]
    - fact_customer_events[Attrition Risk %]
  governance:
    owner: CRM BI
    status: active
    version: v1.2
    last_review: 12.12.2025

- measure_name: NPS Score
  is_kpi_measure: true
  kpi_id_ref: KPI-CUS-003
  semantic_model: CustomerValue_SemanticModel
  display_folder: 02_CX
  category: KPI
  expression:
    logical: NPS Score = (%Promoters - %Detractors) from survey responses in the period.
    aggregation_method: average
  documentation:
    description: Average NPS score across responses in the current context.
    notes: Use survey weights upstream if required.
  dependencies:
    columns:
    - fact_nps[NPS Score]
  governance:
    owner: CX BI
    status: active
    version: v1.2
    last_review: 12.12.2025

- measure_name: Customer Complaints Count
  is_kpi_measure: true
  kpi_id_ref: KPI-SVC-001
  semantic_model: CustomerValue_SemanticModel
  display_folder: 02_CX
  category: KPI
  expression:
    logical: Customer Complaints Count = Count of complaint records in the complaint/service system.
    aggregation_method: count
  documentation:
    description: Total complaint events in the selected context.
    notes: Relies on fact_experience complaint records.
  dependencies:
    columns:
    - fact_experience[Complaint ID]
  governance:
    owner: CX BI
    status: active
    version: v1.2
    last_review: 12.12.2025

- measure_name: COGS Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: CustomerValue_SemanticModel
  display_folder: 02_Margin
  category: Supporting
  expression:
    logical: COGS Amount = SUM(fact_sales[Cost of Goods Sold Amount])
    aggregation_method: sum
  documentation:
    description: Cost of goods sold aggregated for the current filter context.
    notes: ''
  dependencies:
    columns:
    - fact_sales[Cost of Goods Sold Amount]
  governance:
    owner: CRM BI
    status: active
    version: v1.2
    last_review: 12.12.2025

- measure_name: Margin Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: CustomerValue_SemanticModel
  display_folder: 02_Margin
  category: Supporting
  expression:
    logical: Margin Amount = [Net Sales Amount] / [COGS Amount]
    aggregation_method: sum
  documentation:
    description: Margin amount calculated as Net Sales minus COGS.
    notes: ''
  dependencies:
    measures:
    - Net Sales Amount
    - COGS Amount
  governance:
    owner: CRM BI
    status: active
    version: v1.2
    last_review: 12.12.2025

- measure_name: Gross Margin %
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: CustomerValue_SemanticModel
  display_folder: 02_Margin
  category: Supporting
  expression:
    logical: Gross Margin % = ([Net Sales Amount] - [Cost of Goods Sold Amount]) / ([Net Sales Amount])
    aggregation_method: ratio
  documentation:
    description: Gross margin percentage derived from margin and net sales.
    notes: Supporting only; not a required KPI in CustomerValue scope.
  dependencies:
    measures:
    - Margin Amount
    - Net Sales Amount
  governance:
    owner: CRM BI
    status: active
    version: v1.2
    last_review: 12.12.2025

- measure_name: Complaint Rate %
  is_kpi_measure: true
  kpi_id_ref: KPI-QUA-004
  semantic_model: CustomerValue_SemanticModel
  display_folder: 02_CX
  category: KPI
  expression:
    logical: Complaint Rate % = (Complaints) / (ShippedUnits)
    aggregation_method: ratio
  documentation:
    description: Complaint incidence rate.
    notes: Requires interaction base definition.
  dependencies:
    columns:
    - fact_experience[Complaint ID]
    - fact_experience[Interaction ID]
  governance:
    owner: CX BI
    status: active
    version: v1.0
    last_review: TBD

- measure_name: Active Customers
  is_kpi_measure: true
  kpi_id_ref: KPI-CUS-006
  semantic_model: CustomerValue_SemanticModel
  display_folder: 01_Retention
  category: KPI
  expression:
    logical: Active Customers = Distinct customers with at least one qualifying transaction in the period.
    aggregation_method: sum
  documentation:
    description: Alias for Active Customers Count (TMDL display name).
    notes: Same as Active Customers Count.
  dependencies:
    columns: []
  governance:
    owner: CRM BI
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Churned Customers
  is_kpi_measure: true
  kpi_id_ref: KPI-CUS-004
  semantic_model: CustomerValue_SemanticModel
  display_folder: 01_Retention
  category: KPI
  expression:
    logical: Churned Customers = Distinct customers with no qualifying transactions in the current period but active in the look-back window.
    aggregation_method: sum
  documentation:
    description: Alias for Churned Customers Count (TMDL display name).
    notes: Same as Churned Customers Count.
  dependencies:
    columns: []
  governance:
    owner: CRM BI
    status: active
    version: v1.2
    last_review: TBD

- measure_name: CLV
  is_kpi_measure: true
  kpi_id_ref: KPI-CUS-001
  semantic_model: CustomerValue_SemanticModel
  display_folder: 04_Customer
  category: KPI
  expression:
    logical: CLV = Sum of expected future gross margin per customer discounted over the chosen time horizon.
    aggregation_method: sum
  documentation:
    description: Alias for Customer Lifetime Value Amount (TMDL display name).
    notes: Same as Customer Lifetime Value Amount.
  dependencies:
    columns: []
  governance:
    owner: CRM BI
    status: active
    version: v1.2
    last_review: TBD
```


