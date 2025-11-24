# Capacity Utilization ? Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_production
  grain: line_shift
  primary_key:
  - PlantID
  - LineID
  - ShiftDate
  - Shift
  required_columns:
  - name: PlantID
    type: string
    role: org_key
  - name: LineID
    type: string
    role: line_key
  - name: ShiftDate
    type: date
    role: date_key
  - name: Shift
    type: string
    role: attribute
  - name: PlannedHours
    type: decimal
    role: amount
  - name: DowntimeHours
    type: decimal
    role: amount
  - name: OutputUnits
    type: decimal
    role: quantity
  - name: GoodUnits
    type: decimal
    role: quantity
  - name: IdealCycleTime
    type: decimal
    role: helper
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
  - name: Plant
    type: string
- name: dim_line
  grain: line
  primary_key:
  - LineID
  required_columns:
  - name: LineName
    type: string
  - name: LineType
    type: string
relationships:
- from: fact_production.ShiftDate
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_production.PlantID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_production.LineID
  to: dim_line.LineID
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- Downtime Hours: fact_production[DowntimeHours]
- Planned Hours: fact_production[PlannedHours]
- Output Units: fact_production[OutputUnits]
- Good Units: fact_production[GoodUnits]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- RI_OK
- Utilization_Within_0_100
- Hours_Reconcile

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
