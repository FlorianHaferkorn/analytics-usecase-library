# Customer Lifetime Value Analysis - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_customer_transactions
  grain: customer_period
  primary_key:
  - CustomerID
  - PeriodKey
  required_columns:
  - name: CustomerID
    type: string
    role: customer_key
  - name: PeriodKey
    type: string
    role: period_key
  - name: Net Sales Amount
    type: decimal
    role: amount
  - name: COGS Amount
    type: decimal
    role: amount
  - name: Margin Amount
    type: decimal
    role: amount
  - name: Status
    type: string
    role: attribute
  - name: At-Risk Flag
    type: bool
    role: indicator
  - name: Reactivated Flag
    type: bool
    role: indicator
- name: fact_customer_clv
  grain: customer
  primary_key:
  - CustomerID
  required_columns:
  - name: CustomerID
    type: string
    role: customer_key
  - name: CLV Amount
    type: decimal
    role: amount
dims:
- name: dim_customer
  grain: customer
  primary_key:
  - CustomerID
  required_columns:
  - name: CustomerGroup
    type: string
  - name: CustomerName
    type: string
  - name: ChannelDefault
    type: string
- name: dim_period
  grain: period
  primary_key:
  - PeriodKey
  required_columns:
  - name: Year
    type: int
  - name: Quarter
    type: string
  - name: Month
    type: int
relationships:
- from: fact_customer_transactions.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_customer_transactions.PeriodKey
  to: dim_period.PeriodKey
  cardinality: many-to-one
  direction: single
- from: fact_customer_clv.CustomerID
  to: dim_customer.CustomerID
  cardinality: one-to-one
  direction: single
```

## 2. Semantic Model Requirements
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Required conform dimensions as per data contract.
- Relationships follow the structure listed above (single-direction many-to-one).
- Ensure role-playing dates/channel dimensions as needed for customer journeys.

## 3. Measures (DAX + Description)
Following KPIs need measures (DAX to be provided separately):
- CLV (Customer Lifetime Value) (ID: crm.clv.amount)
- Customer Retention % (ID: crm.retention.pct)
- Churn % (ID: crm.churn.pct)
- Reactivation Rate % (ID: crm.reactivation.pct)
- At-Risk Share % (ID: crm.at_risk_share.pct)
- Active Customers Start (ID: crm.active_customers_start.count)
- Active Customers End (ID: crm.active_customers_end.count)
- Lost Customers Count (ID: crm.churned_customers.count)
- Reactivated Customers Count (ID: crm.reactivated_customers.count)
- At-Risk Customers Count (ID: crm.at_risk_customers.count)
- Active Customers (ID: crm.active_customers.count)

## 4. Defaults & Formatting
- Apply appropriate format strings (Currency, %, whole numbers) per KPI.
- Provide display folders (e.g., 01_Customer, 02_Journey).
- Set data categories for Customer, Channel, Touchpoint columns.

## 5. Visual / Interaction Requirements
- Map each visual (cards, trends, heatmaps) to required fields and measures.
- Specify sort-by columns for segment hierarchies.
- Define tooltips/drill-through targets for survey comments or journeys.

## 6. Performance & Refresh
- Refresh cadence aligned with survey uploads (daily/weekly).
- Storage mode: Import.
- Partitioning by survey month where volumes are high.

## 7. RLS/OLS Requirements
- Customer/Region-based RLS as per dim_customer attributes.
- Optional channel-based restrictions for partner views.

## 8. QA & Validation Rules
- RI_OK
- CLV_Model_Documented
- CLV_Reconciles_to_Margin

## 9. Model Mapping Reference
- Margin Amount -> fact_customer_transactions[Margin Amount]
- Net Sales Amount -> fact_customer_transactions[Net Sales Amount]
- COGS Amount -> fact_customer_transactions[COGS Amount]
- Customer -> dim_customer[CustomerID]
- Period -> dim_period[PeriodKey]
