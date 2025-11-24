# Inventory Turnover & Days in Inventory (DIO) ? Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_inventory
  grain: sku_org_period
  primary_key:
  - InventoryID
  required_columns:
  - name: Average Inventory Value
    type: decimal
    role: amount
  - name: Inventory Units Qty
    type: decimal
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
- name: fact_cogs
  grain: sku_org_period
  primary_key:
  - CogsID
  required_columns:
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
- from: fact_inventory.Date
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
- from: fact_cogs.Date
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_cogs.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_cogs.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- Average Inventory Value: fact_inventory[Average Inventory Value]
- Inventory Units Qty: fact_inventory[Inventory Units Qty]
- COGS Amount: fact_cogs[COGS Amount]
- Date: dim_date[Date]
- Org: dim_org[OrgID]
- Product: dim_product[ProductID]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- RI_OK
- Inventory_Value_Positive
- Coverage_InRange

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
