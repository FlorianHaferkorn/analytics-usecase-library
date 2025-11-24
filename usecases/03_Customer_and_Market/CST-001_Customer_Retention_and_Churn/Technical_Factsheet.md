# Customer Retention & Churn Analysis - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_customer_transactions
  grain: customer_day
  primary_key:
  - CustomerID
  - Date
  required_columns:
  - name: CustomerID
    type: string
    role: customer_key
  - name: Date
    type: date
    role: date_key
  - name: Net Sales Amount
    type: decimal
    role: amount
  - name: Margin Amount
    type: decimal
    role: amount
  - name: Units Qty
    type: int
    role: quantity
  - name: Channel
    type: string
    role: channel
- name: fact_customer_profile
  grain: customer_month
  primary_key:
  - CustomerID
  - SnapshotMonth
  required_columns:
  - name: SnapshotMonth
    type: date
    role: date_key
  - name: Segment
    type: string
    role: segment
  - name: LoyaltyTier
    type: string
    role: attribute
  - name: Last Purchase Date
    type: date
    role: helper
  - name: Visit Frequency
    type: decimal
    role: helper
  - name: Basket Size
    type: decimal
    role: helper
  - name: Churn Flag
    type: bool
    role: indicator
dims:
- name: dim_customer
  grain: customer
  primary_key:
  - CustomerID
  required_columns:
  - name: Region
    type: string
  - name: Market
    type: string
  - name: AcquisitionChannel
    type: string
- name: dim_date
  grain: date
  primary_key:
  - Date
relationships:
- from: fact_customer_transactions.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_customer_transactions.Date
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_customer_profile.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_customer_profile.SnapshotMonth
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
- Retention % (ID: crm.retention.pct)
- Churn % (ID: crm.churn.pct)
- CLV (Customer Lifetime Value) (ID: crm.clv.amount)
- Reactivation Rate % (ID: crm.reactivation.pct)
- At-Risk Share % (ID: crm.at_risk_share.pct)

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
- Retention_Range
- Customer_Key_Unique

## 9. Model Mapping Reference
- Customer ID -> dim_customer[CustomerID]
- Region -> dim_customer[Region]
- Market -> dim_customer[Market]
- Net Sales Amount -> fact_customer_transactions[Net Sales Amount]
- Margin Amount -> fact_customer_transactions[Margin Amount]
- Last Purchase Date -> fact_customer_profile[Last Purchase Date]
- Visit Frequency -> fact_customer_profile[Visit Frequency]
- Basket Size -> fact_customer_profile[Basket Size]
- Churn Flag -> fact_customer_profile[Churn Flag]
- Date -> dim_date[Date]
