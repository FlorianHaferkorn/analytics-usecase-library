# Segment Profitability - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_customer_profitability
  grain: customer_period
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
  - name: COGS Amount
    type: decimal
    role: amount
  - name: Service Cost Amount
    type: decimal
    role: amount
  - name: Marketing Cost Amount
    type: decimal
    role: amount
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
  - name: Segment
    type: string
  - name: LoyaltyTier
    type: string
- name: dim_date
  grain: date
  primary_key:
  - Date
relationships:
- from: fact_customer_profitability.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_customer_profitability.Date
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
- Customer Segment Margin Amount (ID: margin.customer.amount)
- Customer Segment Margin % (ID: margin.customer.pct)
- Customer Lifetime Value (CLV) (ID: crm.clv.amount)
- Customer Retention % (ID: crm.retention.pct)

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
- Segment_Assignment_Complete
- Margin_Within_Range

## 9. Model Mapping Reference
- Net Sales Amount -> fact_customer_profitability[Net Sales Amount]
- COGS Amount -> fact_customer_profitability[COGS Amount]
- Service Cost Amount -> fact_customer_profitability[Service Cost Amount]
- Marketing Cost Amount -> fact_customer_profitability[Marketing Cost Amount]
- Customer ID -> dim_customer[CustomerID]
- Segment -> dim_customer[Segment]
- Date -> dim_date[Date]
