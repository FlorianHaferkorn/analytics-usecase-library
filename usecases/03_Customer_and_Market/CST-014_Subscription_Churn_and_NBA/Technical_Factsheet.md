# Subscription Churn & Next-Best-Action - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_subscription
  grain: subscription_period
  primary_key:
  - SubscriptionID
  - Period
  required_columns:
  - name: Period
    type: date
    role: date_key
  - name: SubscriptionID
    type: string
    role: attribute
  - name: CustomerID
    type: string
    role: customer_key
  - name: Plan
    type: string
    role: attribute
  - name: MRR Amount
    type: decimal
    role: amount
  - name: Active Flag
    type: bool
    role: indicator
  - name: Churn Flag
    type: bool
    role: indicator
- name: fact_customer_metrics
  grain: customer_period
  primary_key:
  - CustomerID
  - Period
  required_columns:
  - name: Period
    type: date
    role: date_key
  - name: CustomerID
    type: string
    role: customer_key
  - name: CLV Amount
    type: decimal
    role: amount
dims:
- name: dim_date
  grain: date
  primary_key:
  - Date
  required_columns:
  - name: Year
    type: int
  - name: Quarter
    type: int
  - name: Month
    type: int
- name: dim_customer
  grain: customer
  primary_key:
  - CustomerID
  required_columns:
  - name: Segment
    type: string
  - name: LifecycleStage
    type: string
relationships:
- from: fact_subscription.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_subscription.Period
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_customer_metrics.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_customer_metrics.Period
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
```

## 2. Semantic Model Requirements
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Required conform dimensions as per data contract.
- Relationships follow the structure listed above (single-direction many-to-one).
- Ensure role-playing dates/channel dimensions as needed for customer journeys.

## 3. Measures (DAX + Description)
Following KPIs need measures (DAX to be provided separately):
- Customer Lifetime Value (CLV) Amount (ID: crm.clv.amount)
- Customer Retention % (ID: crm.retention.pct)
- Customer Churn Rate % (ID: crm.churn.pct)

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
- Subscription_Status_Consistent
- Churn_Definition_Documented

## 9. Model Mapping Reference
- MRR Amount -> fact_subscription[MRR Amount]
- CLV Amount -> fact_customer_metrics[CLV Amount]
- Customer -> dim_customer[CustomerID]
- Date -> dim_date[Date]
