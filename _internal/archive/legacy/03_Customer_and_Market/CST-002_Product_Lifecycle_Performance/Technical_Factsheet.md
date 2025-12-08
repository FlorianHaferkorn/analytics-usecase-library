# Product Lifecycle Performance - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_sales
  grain: invoice_line
  primary_key:
  - InvoiceLineID
  required_columns:
  - name: Date
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: ProductID
    type: string
    role: product_key
  - name: Net Sales Amount
    type: decimal
    role: amount
  - name: COGS Amount
    type: decimal
    role: amount
  - name: Promo Cost Amount
    type: decimal
    role: amount
  - name: Channel
    type: string
    role: channel
- name: fact_product_investment
  grain: product
  primary_key:
  - ProductID
  required_columns:
  - name: LaunchDate
    type: date
    role: date_key
  - name: DevelopmentCost
    type: decimal
    role: amount
  - name: MarketingCost
    type: decimal
    role: amount
  - name: LifecycleStage
    type: string
    role: attribute
dims:
- name: dim_product
  grain: product
  primary_key:
  - ProductID
  required_columns:
  - name: Category
    type: string
  - name: Subcategory
    type: string
  - name: Brand
    type: string
  - name: Status
    type: string
- name: dim_org
  grain: org
  primary_key:
  - OrgID
- name: dim_date
  grain: date
  primary_key:
  - Date
relationships:
- from: fact_sales.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_sales.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_sales.Date
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_product_investment.ProductID
  to: dim_product.ProductID
  cardinality: one-to-one
  direction: both
```

## 2. Semantic Model Requirements
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Required conform dimensions as per data contract.
- Relationships follow the structure listed above (single-direction many-to-one).
- Ensure role-playing dates/channel dimensions as needed for customer journeys.

## 3. Measures (DAX + Description)
Following KPIs need measures (DAX to be provided separately):
- New Product Share % (ID: prod.lifecycle.new_share.pct)
- Product Contribution Margin % (ID: prod.contribution_margin.pct)
- Lifecycle Age (months) (ID: prod.lifecycle.age.months)
- Product ROI % (ID: prod.roi.pct)
- Phase Distribution % (ID: prod.lifecycle.phase_distribution.pct)

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
- LaunchDate_Present
- Phase_Coverage_Complete

## 9. Model Mapping Reference
- Net Sales Amount -> fact_sales[Net Sales Amount]
- COGS Amount -> fact_sales[COGS Amount]
- Promo Cost Amount -> fact_sales[Promo Cost Amount]
- Development Cost -> fact_product_investment[DevelopmentCost]
- Marketing Cost -> fact_product_investment[MarketingCost]
- Launch Date -> fact_product_investment[LaunchDate]
- Lifecycle Stage -> fact_product_investment[LifecycleStage]
- Product -> dim_product[ProductID]
- Date -> dim_date[Date]
- Org -> dim_org[OrgID]
