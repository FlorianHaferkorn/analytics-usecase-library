# Auto-Replenishment Engine ? Technical Factsheet

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
  - name: Units Qty
    type: decimal
    role: quantity
- name: fact_forecast
  grain: forecast_line
  primary_key:
  - ForecastLineID
  required_columns:
  - name: Forecast Version
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
  - name: Forecast Units Qty
    type: decimal
    role: quantity
- name: fact_inventory
  grain: org_product_day
  primary_key:
  - OrgID
  - ProductID
  - Date
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
  - name: On Hand Units Qty
    type: decimal
    role: quantity
- name: fact_replenishment_plan
  grain: org_product_day
  primary_key:
  - OrgID
  - ProductID
  - Date
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
  - name: Planned Order Units Qty
    type: decimal
    role: quantity
  - name: Actual Order Units Qty
    type: decimal
    role: quantity
- name: fact_service_level
  grain: org_product_period
  primary_key:
  - OrgID
  - ProductID
  - Period
  required_columns:
  - name: Period
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: ProductID
    type: string
    role: product_key
  - name: Order Lines Total
    type: int
    role: quantity
  - name: Order Lines Stockout
    type: int
    role: quantity
  - name: Order Lines OTIF
    type: int
    role: quantity
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
  - name: Week
    type: int
- name: dim_org
  grain: org
  primary_key:
  - OrgID
  required_columns:
  - name: Region
    type: string
  - name: Site
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
  - name: Lead Time Days
    type: int
  - name: Min Stock Units
    type: decimal
  - name: Max Stock Units
    type: decimal
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
- from: fact_inventory.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_inventory.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_inventory.Date
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_replenishment_plan.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_replenishment_plan.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_replenishment_plan.Date
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_service_level.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_service_level.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_service_level.Period
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- Net Sales Amount: fact_sales[Net Sales Amount]
- Units Qty: fact_sales[Units Qty]
- Forecast Units Qty: fact_forecast[Forecast Units Qty]
- On Hand Units Qty: fact_inventory[On Hand Units Qty]
- Planned Order Units Qty: fact_replenishment_plan[Planned Order Units Qty]
- Actual Order Units Qty: fact_replenishment_plan[Actual Order Units Qty]
- Order Lines Total: fact_service_level[Order Lines Total]
- Order Lines Stockout: fact_service_level[Order Lines Stockout]
- Order Lines OTIF: fact_service_level[Order Lines OTIF]
- Date: dim_date[Date]
- Org: dim_org[OrgID]
- Product: dim_product[ProductID]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Forecast_Version_Frozen
- LeadTime_Defined
- MinMax_Policy_Documented

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
