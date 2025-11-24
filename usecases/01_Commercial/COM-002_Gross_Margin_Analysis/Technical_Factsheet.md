# Gross Margin % vs Plan & Last Year ? Technical Factsheet

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
  - name: Channel
    type: string
    role: channel
dims:
- name: dim_date
  grain: date
  primary_key:
  - Date
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
- COGS Amount: fact_sales[COGS Amount]
- Price Realization %: [Price Realization %]
- Date: dim_date[Date]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- RI_OK
- GM_PositivePlan

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
