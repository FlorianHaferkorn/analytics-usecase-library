# Cross-Sell & Basket Analysis - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_sales
  grain: transaction_line
  primary_key:
  - TransactionID
  - LineID
  required_columns:
  - name: TransactionID
    type: string
    role: attribute
  - name: CustomerID
    type: string
    role: customer_key
  - name: Date
    type: date
    role: date_key
  - name: Net Sales Amount
    type: decimal
    role: amount
  - name: Units Qty
    type: int
    role: quantity
  - name: Channel
    type: string
    role: channel
  - name: Category
    type: string
    role: attribute
  - name: Subcategory
    type: string
    role: attribute
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
- Cross-Sell Ratio % (ID: crm.cross_sell_ratio.pct)
- Average Basket Value (ID: crm.basket_size.amount)
- Average Basket Units (ID: crm.basket_size.units)

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
- Customer_Key_Unique
- Basket_Size_InRange

## 9. Model Mapping Reference
- Transaction ID -> fact_sales[TransactionID]
- Customer ID -> dim_customer[CustomerID]
- Net Sales Amount -> fact_sales[Net Sales Amount]
- Units Qty -> fact_sales[Units Qty]
- Category -> fact_sales[Category]
- Subcategory -> fact_sales[Subcategory]
- Channel -> fact_sales[Channel]
- Date -> dim_date[Date]
