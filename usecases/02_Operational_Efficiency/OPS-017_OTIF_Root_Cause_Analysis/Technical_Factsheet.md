# OTIF Root Cause Analysis ? Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_deliveries
  grain: delivery
  primary_key:
  - DeliveryID
  required_columns:
  - name: DeliveryID
    type: string
    role: attribute
  - name: Planned Delivery Date
    type: date
    role: date_key
  - name: Actual Delivery Date
    type: date
    role: helper
  - name: OrgID
    type: string
    role: org_key
  - name: CustomerID
    type: string
    role: customer_key
  - name: Delivered Lines Total
    type: int
    role: quantity
  - name: Delivered Lines OTIF
    type: int
    role: quantity
  - name: Delivered Lines Inaccurate
    type: int
    role: quantity
  - name: Delivery Issue Code
    type: string
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
- name: dim_customer
  grain: customer
  primary_key:
  - CustomerID
  required_columns:
  - name: Segment
    type: string
relationships:
- from: fact_deliveries."Planned Delivery Date"
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_deliveries.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_deliveries.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- Delivered Lines Total: fact_deliveries[Delivered Lines Total]
- Delivered Lines OTIF: fact_deliveries[Delivered Lines OTIF]
- Delivered Lines Inaccurate: fact_deliveries[Delivered Lines Inaccurate]
- Date: dim_date[Date]
- Org: dim_org[OrgID]
- Customer: dim_customer[CustomerID]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- OTIF_Definition_Documented
- Event_Codes_Defined

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
