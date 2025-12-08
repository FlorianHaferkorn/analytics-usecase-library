# Route Optimization & Transport Cost Modeling ? Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_transport
  grain: shipment
  primary_key:
  - ShipmentID
  required_columns:
  - name: ShipmentID
    type: string
    role: attribute
  - name: Route ID
    type: string
    role: attribute
  - name: Departure Date
    type: date
    role: date_key
  - name: Transport Cost Amount
    type: decimal
    role: amount
  - name: Shipped Units Qty
    type: decimal
    role: quantity
  - name: Distance Km
    type: decimal
    role: attribute
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
  - name: Distribution Center
    type: string
- name: dim_route
  grain: route
  primary_key:
  - Route ID
  required_columns:
  - name: Route Name
    type: string
  - name: Transport Mode
    type: string
relationships:
- from: fact_transport."Departure Date"
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- Transport Cost Amount: fact_transport[Transport Cost Amount]
- Shipped Units Qty: fact_transport[Shipped Units Qty]
- Distance Km: fact_transport[Distance Km]
- Route ID: fact_transport[Route ID]
- Route Name: dim_route[Route Name]
- Date: dim_date[Date]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Transport_Cost_Allocation_Documented
- Route_Master_Consistent

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
