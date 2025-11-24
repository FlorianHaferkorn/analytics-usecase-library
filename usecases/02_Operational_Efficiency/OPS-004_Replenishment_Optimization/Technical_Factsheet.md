# Replenishment Optimization & Service Level Management ? Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_replenishment_order
  grain: order_line
  primary_key:
  - OrderID
  - OrderLine
  required_columns:
  - name: OrderDate
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: ProductID
    type: string
    role: product_key
  - name: SupplierID
    type: string
    role: supplier_key
  - name: Order Qty
    type: decimal
    role: quantity
  - name: Forecast Qty
    type: decimal
    role: quantity
  - name: Safety Stock Qty
    type: decimal
    role: helper
  - name: Reorder Point Qty
    type: decimal
    role: helper
  - name: Lead Time Days
    type: int
    role: helper
- name: fact_fulfillment
  grain: delivery_line
  primary_key:
  - DeliveryID
  - DeliveryLine
  required_columns:
  - name: DeliveryDate
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: ProductID
    type: string
    role: product_key
  - name: Delivered Qty
    type: decimal
    role: quantity
  - name: Demand Qty
    type: decimal
    role: quantity
  - name: Stock-Out Flag
    type: bool
    role: indicator
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
- name: dim_supplier
  grain: supplier
  primary_key:
  - SupplierID
relationships:
- from: fact_replenishment_order.OrderDate
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_replenishment_order.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_replenishment_order.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_fulfillment.DeliveryDate
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_fulfillment.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_fulfillment.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_replenishment_order.SupplierID
  to: dim_supplier.SupplierID
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- Order Qty: fact_replenishment_order[Order Qty]
- Delivered Qty: fact_fulfillment[Delivered Qty]
- Demand Qty: fact_fulfillment[Demand Qty]
- Forecast Qty: fact_replenishment_order[Forecast Qty]
- Safety Stock Qty: fact_replenishment_order[Safety Stock Qty]
- Reorder Point Qty: fact_replenishment_order[Reorder Point Qty]
- Lead Time Days: fact_replenishment_order[Lead Time Days]
- Date: dim_date[Date]
- Org: dim_org[OrgID]
- Product: dim_product[ProductID]
- Supplier: dim_supplier[SupplierID]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- RI_OK
- ServiceLevel_Bounds
- LeadTime_Positive

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
