# Predictive Maintenance & Auto-Dispatch ? Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_mes_events
  grain: event
  primary_key:
  - EventID
  required_columns:
  - name: EventID
    type: string
    role: attribute
  - name: AssetID
    type: string
    role: attribute
  - name: StartTime
    type: datetime
    role: date_key
  - name: EndTime
    type: datetime
    role: helper
  - name: Event Type
    type: string
    role: attribute
  - name: Failure Code
    type: string
    role: attribute
- name: fact_maintenance_orders
  grain: maintenance_order
  primary_key:
  - OrderID
  required_columns:
  - name: OrderID
    type: string
    role: attribute
  - name: AssetID
    type: string
    role: attribute
  - name: Order Type
    type: string
    role: attribute
  - name: TechnicianID
    type: string
    role: attribute
  - name: Planned Start
    type: datetime
    role: date_key
  - name: Actual Start
    type: datetime
    role: helper
  - name: Actual End
    type: datetime
    role: helper
  - name: Maintenance Cost Amount
    type: decimal
    role: amount
- name: fact_production
  grain: production_run
  primary_key:
  - RunID
  required_columns:
  - name: RunID
    type: string
    role: attribute
  - name: AssetID
    type: string
    role: attribute
  - name: Planned Qty
    type: decimal
    role: quantity
  - name: Produced Qty
    type: decimal
    role: quantity
  - name: Good Qty
    type: decimal
    role: quantity
  - name: Run Start
    type: datetime
    role: date_key
  - name: Run End
    type: datetime
    role: helper
dims:
- name: dim_org
  grain: org
  primary_key:
  - OrgID
  required_columns:
  - name: Region
    type: string
  - name: Site
    type: string
- name: dim_asset
  grain: asset
  primary_key:
  - AssetID
  required_columns:
  - name: Asset Family
    type: string
  - name: Criticality
    type: string
relationships:
- from: fact_mes_events.AssetID
  to: dim_asset.AssetID
  cardinality: many-to-one
  direction: single
- from: fact_maintenance_orders.AssetID
  to: dim_asset.AssetID
  cardinality: many-to-one
  direction: single
- from: fact_production.AssetID
  to: dim_asset.AssetID
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- Downtime Hours: fact_mes_events[Downtime Hours]
- Maintenance Cost Amount: fact_maintenance_orders[Maintenance Cost Amount]
- Planned Qty: fact_production[Planned Qty]
- Produced Qty: fact_production[Produced Qty]
- Good Qty: fact_production[Good Qty]
- Asset: dim_asset[AssetID]
- Org: dim_org[OrgID]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Asset_ID_Consistent
- Failure_Codes_Defined

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
