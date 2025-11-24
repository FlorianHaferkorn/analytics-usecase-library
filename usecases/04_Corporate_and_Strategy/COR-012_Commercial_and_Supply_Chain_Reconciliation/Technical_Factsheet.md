# Commercial & Supply Chain Reconciliation - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_sales
  grain: invoice_line
  primary_key:
  - InvoiceLineID
  required_columns:
  - name: Net Sales Amount
    type: decimal
    role: amount
  - name: Date
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: ProductID
    type: string
    role: product_key
  - name: Promo Flag
    type: bool
    role: indicator
  - name: Promo ID
    type: string
    role: attribute
- name: fact_inventory
  grain: org_product_period
  primary_key:
  - OrgID
  - ProductID
  - Period
  required_columns:
  - name: Period
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: ProductID
    type: string
    role: product_key
  - name: Inventory Amount
    type: decimal
    role: amount
  - name: Inventory Units Qty
    type: decimal
    role: quantity
- name: fact_service_level
  grain: org_product_period
  primary_key:
  - OrgID
  - ProductID
  - Period
  required_columns:
  - name: Period
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: ProductID
    type: string
    role: product_key
  - name: Order Lines Total
    type: int
    role: quantity
  - name: Order Lines Stockout
    type: int
    role: quantity
- name: fact_working_capital
  grain: org_period_wc
  primary_key:
  - OrgID
  - Period
  required_columns:
  - name: Period
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: DSO Days
    type: decimal
    role: helper
  - name: DPO Days
    type: decimal
    role: helper
  - name: DIO Days
    type: decimal
    role: helper
dims:
- name: dim_date
  grain: date
  primary_key:
  - Date
  required_columns:
  - name: Year
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
- name: dim_product
  grain: product
  primary_key:
  - ProductID
  required_columns:
  - name: Category
    type: string
  - name: Subcategory
    type: string
relationships:
- from: fact_sales.Date
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_sales.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_sales.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_inventory.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_inventory.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_inventory.Period
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_service_level.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_service_level.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_service_level.Period
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_working_capital.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_working_capital.Period
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
```

## 2. Semantic Model Requirements
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Required facts/dims per contract above.
- Ensure relationships are single-direction many-to-one (role-playing dates if needed).
- Provide conformed Org/Product/Initiative hierarchies.

## 3. Measures (DAX + Description)
Following KPIs require measures (DAX delivered separately):
- Net Sales Amount (ID: sales.net_sales.amount)
- Promo ROI % (ID: sales.promo.roi.pct)
- Promo Uplift % (ID: sales.promo.uplift_pct)
- Incremental GM Amount (ID: margin.promo.incremental.amount)
- Stockout Rate % (ID: ops.stockout.pct)
- Inventory Days on Hand (DIO) (ID: ops.inventory.days)
- Inventory Turnover (ID: ops.inventory.turnover)
- Cash Conversion Cycle (Days) (ID: ops.working_capital.ccc.days)

## 4. Defaults & Formatting
- Apply correct format strings (currency, %, integer).
- Use display folders (01_Strategic, 02_Variance, etc.).
- Set data categories for Org/Initiative/Timeline fields.

## 5. Visual / Interaction Requirements
- Map visuals (cards, bridges, funnels) to required fields.
- Define drill paths for Org, Initiative, Time.
- Specify tooltip fields and sort-by logic.

## 6. Performance & Refresh
- Storage mode: Import (unless monthly snapshot suggests Hybrid).
- Refresh cadence aligned with corporate close cadence.
- Partitioning by FiscalPeriod where data volume is high.

## 7. RLS/OLS Requirements
- Org-based RLS (Region/Entity).
- Optional Initiative-based restrictions for project owners.

## 8. QA & Validation Rules
- Promo_Flag_Consistent
- Forecast_Version_Frozen
- Inventory_Valuation_Reconciles

## 9. Model Mapping Reference
- Net Sales Amount -> fact_sales[Net Sales Amount]
- Promo Flag -> fact_sales[Promo Flag]
- Promo ID -> fact_sales[Promo ID]
- Inventory Amount -> fact_inventory[Inventory Amount]
- Inventory Units Qty -> fact_inventory[Inventory Units Qty]
- Order Lines Total -> fact_service_level[Order Lines Total]
- Order Lines Stockout -> fact_service_level[Order Lines Stockout]
- Date -> dim_date[Date]
- Org -> dim_org[OrgID]
- Product -> dim_product[ProductID]
