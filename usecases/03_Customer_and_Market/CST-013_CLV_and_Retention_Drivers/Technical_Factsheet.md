# CLV & Retention Drivers - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
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
  - name: Active Flag
    type: bool
    role: indicator
  - name: Churn Flag
    type: bool
    role: indicator
- name: fact_sales
  grain: invoice_line
  primary_key:
  - InvoiceLineID
  required_columns:
  - name: Net Sales Amount
    type: decimal
    role: amount
  - name: Units Qty
    type: int
    role: quantity
  - name: Date
    type: date
    role: date_key
  - name: CustomerID
    type: string
    role: customer_key
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
- name: dim_org
  grain: org
  primary_key:
  - OrgID
  required_columns:
  - name: Region
    type: string
  - name: BusinessUnit
    type: string
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
- from: fact_customer_metrics.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_customer_metrics.Period
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_sales.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_sales.Date
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
- Average Basket Value (ID: crm.basket_size.amount)
- Average Basket Units (ID: crm.basket_size.units)
- Cross-Sell Ratio % (ID: crm.cross_sell_ratio.pct)

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
- Customer_ID_Consistent
- Lifecycle_Stage_Defined

## 9. Model Mapping Reference
- CLV Amount -> fact_customer_metrics[CLV Amount]
- Net Sales Amount -> fact_sales[Net Sales Amount]
- Units Qty -> fact_sales[Units Qty]
- Customer -> dim_customer[CustomerID]
- Date -> dim_date[Date]
- Org -> dim_org[OrgID]
