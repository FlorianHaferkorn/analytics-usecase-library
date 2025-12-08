# Logistics Cost Ratio ? Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_logistics_cost
  grain: dc_period
  primary_key:
  - CostID
  required_columns:
  - name: Date
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: Transport Cost Amount
    type: decimal
    role: amount
  - name: Warehouse Cost Amount
    type: decimal
    role: amount
  - name: Handling Cost Amount
    type: decimal
    role: amount
- name: fact_logistics_volume
  grain: dc_period
  primary_key:
  - VolumeID
  required_columns:
  - name: Date
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: Shipped Units Qty
    type: decimal
    role: quantity
  - name: Shipped Weight
    type: decimal
    role: helper
  - name: Shipments Count
    type: int
    role: helper
dims:
- name: dim_org
  grain: org
  primary_key:
  - OrgID
  required_columns:
  - name: Region
    type: string
  - name: Country
    type: string
  - name: DC
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
- from: fact_logistics_cost.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_logistics_cost.Date
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_logistics_volume.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_logistics_volume.Date
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- Transport Cost Amount: fact_logistics_cost[Transport Cost Amount]
- Warehouse Cost Amount: fact_logistics_cost[Warehouse Cost Amount]
- Handling Cost Amount: fact_logistics_cost[Handling Cost Amount]
- Shipped Units Qty: fact_logistics_volume[Shipped Units Qty]
- Shipped Weight: fact_logistics_volume[Shipped Weight]
- Shipments Count: fact_logistics_volume[Shipments Count]
- Org: dim_org[OrgID]
- Date: dim_date[Date]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- RI_OK
- Logistics_Cost_Reconciles
- Volume_Measures_Consistent

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
