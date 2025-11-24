# Integrated Margin Bridge (P&L Driver Tree) - Technical Factsheet

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
  - name: COGS Amount
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
- name: fact_pnl
  grain: org_period_pnl
  primary_key:
  - OrgID
  - Period
  - PnLLine
  required_columns:
  - name: Period
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: PnLLine
    type: string
    role: attribute
  - name: Amount
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
- from: fact_pnl.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_pnl.Period
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
- Gross Margin Amount (ID: margin.gm.amount)
- Gross Margin % (ID: margin.gm.pct)
- EBITDA Margin % (ID: profit.ebitda_margin)
- " Net Sales Amount vs LY (ID: sales.net_sales.delta_amount.ly)
- Price Effect Amount (ID: sales.pvm.price_effect.amount)
- Volume Effect Amount (ID: sales.pvm.volume_effect.amount)
- Mix Effect Amount (ID: sales.pvm.mix_effect.amount)
- COGS Amount (ID: cost.cogs.amount)

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
- P&L_Reconciles
- Bridge_Fully_Explained

## 9. Model Mapping Reference
- Net Sales Amount -> fact_sales[Net Sales Amount]
- COGS Amount -> fact_sales[COGS Amount]
- PnL Amount -> fact_pnl[Amount]
- Date -> dim_date[Date]
- Org -> dim_org[OrgID]
- Product -> dim_product[ProductID]
