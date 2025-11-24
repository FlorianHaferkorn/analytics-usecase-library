# Innovation Launch Tracking ? Technical Factsheet

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
  - name: Is New Product
    type: bool
    role: indicator
- name: fact_product_lifecycle
  grain: product_period
  primary_key:
  - ProductID
  - Period
  required_columns:
  - name: Period
    type: date
    role: date_key
  - name: ProductID
    type: string
    role: product_key
  - name: Lifecycle Stage
    type: string
    role: attribute
  - name: New Flag
    type: bool
    role: indicator
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
  - name: Channel
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
- from: fact_product_lifecycle.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_product_lifecycle.Period
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- Net Sales Amount: fact_sales[Net Sales Amount]
- Units Qty: fact_sales[Units Qty]
- Lifecycle Stage: fact_product_lifecycle[Lifecycle Stage]
- Date: dim_date[Date]
- Org: dim_org[OrgID]
- Product: dim_product[ProductID]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Innovation_Flag_Consistent
- Lifecycle_Stage_Defined

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
