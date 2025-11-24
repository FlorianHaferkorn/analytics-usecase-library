# Stockout & Service Level ? Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_orders
  grain: order_line
  primary_key:
  - OrderLineID
  required_columns:
  - name: OrderLineID
    type: string
    role: attribute
  - name: Requested Date
    type: date
    role: date_key
  - name: Delivered Date
    type: date
    role: helper
  - name: Requested Qty
    type: decimal
    role: quantity
  - name: Delivered Qty
    type: decimal
    role: quantity
  - name: Stockout Flag
    type: bool
    role: indicator
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
- name: dim_date
  grain: date
  primary_key:
  - Date
  required_columns:
  - name: Year
    type: int
  - name: Month
    type: int
relationships:
- from: fact_orders.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_orders.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_orders."Requested Date"
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- Requested Qty: fact_orders[Requested Qty]
- Delivered Qty: fact_orders[Delivered Qty]
- Stockout Flag: fact_orders[Stockout Flag]
- Requested Date: fact_orders[Requested Date]
- Org: dim_org[OrgID]
- Product: dim_product[ProductID]
- Channel: fact_orders[Channel]
- Date: dim_date[Date]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- RI_OK
- OTIF_InRange
- Stockout_Events_Tracked

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
