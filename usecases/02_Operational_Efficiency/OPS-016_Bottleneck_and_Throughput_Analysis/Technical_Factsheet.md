# Bottleneck & Throughput Analysis (TOC) ? Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
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
  - name: Produced Units Qty
    type: decimal
    role: quantity
  - name: Good Units Qty
    type: decimal
    role: quantity
  - name: Run Start
    type: datetime
    role: date_key
  - name: Run End
    type: datetime
    role: helper
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
  - name: OEE %
    type: decimal
    role: attribute
  - name: Performance %
    type: decimal
    role: attribute
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
- from: fact_production.AssetID
  to: dim_asset.AssetID
  cardinality: many-to-one
  direction: single
- from: fact_mes_oee.AssetID
  to: dim_asset.AssetID
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- Produced Units Qty: fact_production[Produced Units Qty]
- Good Units Qty: fact_production[Good Units Qty]
- OEE %: fact_mes_oee[OEE %]
- Performance %: fact_mes_oee[Performance %]
- Asset: dim_asset[AssetID]
- Org: dim_org[OrgID]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Asset_ID_Consistent
- Routing_Defined

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
