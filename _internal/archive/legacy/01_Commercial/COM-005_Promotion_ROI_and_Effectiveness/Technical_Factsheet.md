# Promotion ROI & Effectiveness ? Technical Factsheet

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
  - name: Promo Flag
    type: bool
    role: indicator
  - name: Promo ID
    type: string
    role: attribute
  - name: Promo Type
    type: string
    role: attribute
  - name: Promo Cost Amount
    type: decimal
    role: amount
- name: fact_marketing_spend
  grain: promo_campaign
  primary_key:
  - PromoID
  required_columns:
  - name: PromoID
    type: string
    role: attribute
  - name: Planned Promo Cost Amount
    type: decimal
    role: amount
  - name: Channel
    type: string
    role: channel
  - name: Start Date
    type: date
    role: helper
  - name: End Date
    type: date
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
  - name: Area
    type: string
  - name: Store
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
  ri_expected: '>=99.5%'
- from: fact_sales.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_sales.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_marketing_spend.PromoID
  to: fact_sales.PromoID
  cardinality: one-to-many
  direction: single
```

## 2. Model Mapping
- Net Sales Amount: fact_sales[Net Sales Amount]
- Units Qty: fact_sales[Units Qty]
- Promo Flag: fact_sales[Promo Flag]
- Promo ID: fact_sales[Promo ID]
- Promo Type: fact_sales[Promo Type]
- Promo Cost Amount: fact_sales[Promo Cost Amount]
- Date: dim_date[Date]
- Org: dim_org[OrgID]
- Product: dim_product[ProductID]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- RI_OK
- Baseline_Method_Documented
- Promo_Period_Flag_Consistent

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
