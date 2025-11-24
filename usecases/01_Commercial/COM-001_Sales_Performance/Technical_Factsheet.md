# Sales Performance vs Plan & Last Year – Technical Factsheet

## 0. Metadata & KPI Binding
- dataset_model: `Contoso Sales Sample for Power BI Desktop.SemanticModel`
- qa_asserts: `RI_OK`, `DeltaPct_OnlyWhenPlanPositive`
- required_kpi_ids:
  - sales.net_sales.amount
  - sales.net_sales.delta_amount.ly
  - sales.net_sales.delta_pct.ly
  - sales.price.realization_pct
  - sales.promo.uplift_pct
  - sales.pvm.price_effect.amount
  - sales.pvm.volume_effect.amount
  - sales.pvm.mix_effect.amount
  - margin.gm.pct
  - margin.gm.amount
- required_kpis:
  - `sales.net_sales.amount` → Net Sales Amount
  - `sales.net_sales.delta_amount.ly` → Delta Net Sales Amount
  - `sales.net_sales.delta_pct.ly` → Delta% Net Sales
  - `sales.price.realization_pct` → Price Realization %
  - `sales.promo.uplift_pct` → Promo Uplift %
  - `sales.pvm.price_effect.amount` → Price Effect Amount
  - `sales.pvm.volume_effect.amount` → Volume Effect Amount
  - `sales.pvm.mix_effect.amount` → Mix Effect Amount
  - `margin.gm.pct` → Gross Margin %
  - `margin.gm.amount` → Gross Margin Amount


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
  - name: Units Qty
    type: int
    role: quantity
  - name: Date
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: ProductID
    type: string
    role: product_key
  - name: Channel
    type: string
    role: channel
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
- name: dim_product
  grain: product
  primary_key:
  - ProductID
relationships:
- from: fact_sales.Date
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
  ri_expected: '>=99.9%'
- from: fact_sales.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_sales.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- Net Sales Amount: fact_sales[Net Sales Amount]
- Units Qty: fact_sales[Units Qty]
- Date: dim_date[Date]
- Org: dim_org[OrgID]
- Product: dim_product[ProductID]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- QA Assertions:
  - RI_OK
  - DeltaPct_OnlyWhenPlanPositive

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
