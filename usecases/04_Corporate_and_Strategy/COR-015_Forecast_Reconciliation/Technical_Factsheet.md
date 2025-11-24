# Forecast Reconciliation (Bottom-Up " Top-Down) - Technical Factsheet

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
- name: fact_forecast
  grain: forecast_line
  primary_key:
  - ForecastLineID
  required_columns:
  - name: Forecast Version
    type: string
    role: attribute
  - name: Forecast Type
    type: string
    role: attribute
  - name: Forecast Date
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: ProductID
    type: string
    role: product_key
  - name: Forecast Net Sales Amount
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
- from: fact_forecast.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_forecast.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_forecast."Forecast Date"
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
- Net Sales Amount (Forecast) (ID: sales.net_sales.amount.forecast)
- Forecast Accuracy (MAPE %) (ID: sales.forecast.mape_pct)
- Forecast Bias % (ID: sales.forecast.bias_pct)

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
- Forecast_Versions_Defined
- Consensus_Rules_Documented
- Plan_vs_Actual_Reconciles

## 9. Model Mapping Reference
- Net Sales Amount -> fact_sales[Net Sales Amount]
- Forecast Net Sales Amount -> fact_forecast[Forecast Net Sales Amount]
- Date -> dim_date[Date]
- Org -> dim_org[OrgID]
- Product -> dim_product[ProductID]
