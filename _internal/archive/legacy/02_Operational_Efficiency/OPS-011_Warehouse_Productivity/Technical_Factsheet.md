# Warehouse Productivity & Picking Efficiency ? Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_wh_labor
  grain: dc_shift
  primary_key:
  - LaborID
  required_columns:
  - name: Date
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: Shift
    type: string
    role: attribute
  - name: Labor Hours
    type: decimal
    role: helper
  - name: Labor Cost Amount
    type: decimal
    role: amount
- name: fact_wh_activity
  grain: dc_shift
  primary_key:
  - ActivityID
  required_columns:
  - name: Date
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: Shift
    type: string
    role: attribute
  - name: Order Lines Picked
    type: int
    role: helper
  - name: Picks Count
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
  - name: DC
    type: string
  - name: Zone
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
  - name: Day
    type: int
relationships:
- from: fact_wh_labor.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_wh_labor.Date
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_wh_activity.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_wh_activity.Date
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- Labor Hours: fact_wh_labor[Labor Hours]
- Labor Cost Amount: fact_wh_labor[Labor Cost Amount]
- Order Lines Picked: fact_wh_activity[Order Lines Picked]
- Picks Count: fact_wh_activity[Picks Count]
- Org: dim_org[OrgID]
- Date: dim_date[Date]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- RI_OK
- Lines_Per_Hour_InRange
- Labor_Hours_Tracked

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
