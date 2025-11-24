# OEE Advanced & Root Causes ? Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_mes_oee
  grain: asset_day
  primary_key:
  - AssetID
  - Date
  required_columns:
  - name: AssetID
    type: string
    role: attribute
  - name: Date
    type: date
    role: date_key
  - name: Availability %
    type: decimal
    role: attribute
  - name: Performance %
    type: decimal
    role: attribute
  - name: Quality %
    type: decimal
    role: attribute
  - name: OEE %
    type: decimal
    role: attribute
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
  - name: Loss Category
    type: string
    role: attribute
  - name: Loss Reason
    type: string
    role: attribute
  - name: Downtime Hours
    type: decimal
    role: amount
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
  - name: Line
    type: string
relationships:
- from: fact_mes_oee.AssetID
  to: dim_asset.AssetID
  cardinality: many-to-one
  direction: single
- from: fact_mes_events.AssetID
  to: dim_asset.AssetID
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- OEE %: fact_mes_oee[OEE %]
- Availability %: fact_mes_oee[Availability %]
- Performance %: fact_mes_oee[Performance %]
- Quality %: fact_mes_oee[Quality %]
- Downtime Hours: fact_mes_events[Downtime Hours]
- Asset: dim_asset[AssetID]
- Org: dim_org[OrgID]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Asset_ID_Consistent
- Downtime_Codes_Defined

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
