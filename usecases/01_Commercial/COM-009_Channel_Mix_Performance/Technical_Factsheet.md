# Channel Mix Performance ? Technical Factsheet

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
  - name: Gross Margin Amount
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
- Gross Margin Amount: fact_sales[Gross Margin Amount]
- Date: dim_date[Date]
- Org: dim_org[OrgID]
- Product: dim_product[ProductID]
- Channel: fact_sales[Channel]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- RI_OK
- Channel_Share_100
- GM_By_Channel_Consistent

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
