# Brand Equity & Awareness - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_brand_survey
  grain: respondent
  primary_key:
  - RespondentID
  required_columns:
  - name: RespondentID
    type: string
    role: attribute
  - name: Date
    type: date
    role: date_key
  - name: Region
    type: string
    role: attribute
  - name: Country
    type: string
    role: attribute
  - name: Segment
    type: string
    role: attribute
  - name: Brand Awareness Flag
    type: bool
    role: indicator
  - name: Brand Preference Flag
    type: bool
    role: indicator
  - name: NPS Score
    type: int
    role: attribute
dims:
- name: dim_date
  grain: date
  primary_key:
  - Date
  required_columns:
  - name: Year
    type: int
  - name: Quarter
    type: int
```

## 2. Semantic Model Requirements
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Required conform dimensions as per data contract.
- Relationships follow the structure listed above (single-direction many-to-one).
- Ensure role-playing dates/channel dimensions as needed for customer journeys.

## 3. Measures (DAX + Description)
Following KPIs need measures (DAX to be provided separately):
- Brand Awareness % (ID: mkt.brand.awareness.pct)
- Brand Preference % (ID: mkt.brand.preference.pct)
- Net Promoter Score (NPS) (ID: crm.nps.index)

## 4. Defaults & Formatting
- Apply appropriate format strings (Currency, %, whole numbers) per KPI.
- Provide display folders (e.g., 01_Customer, 02_Journey).
- Set data categories for Customer, Channel, Touchpoint columns.

## 5. Visual / Interaction Requirements
- Map each visual (cards, trends, heatmaps) to required fields and measures.
- Specify sort-by columns for segment hierarchies.
- Define tooltips/drill-through targets for survey comments or journeys.

## 6. Performance & Refresh
- Refresh cadence aligned with survey uploads (daily/weekly).
- Storage mode: Import.
- Partitioning by survey month where volumes are high.

## 7. RLS/OLS Requirements
- Customer/Region-based RLS as per dim_customer attributes.
- Optional channel-based restrictions for partner views.

## 8. QA & Validation Rules
- RI_OK
- Survey_Base_Sufficient
- Brand_Metrics_Consistent

## 9. Model Mapping Reference
- Brand Awareness Flag -> fact_brand_survey[Brand Awareness Flag]
- Brand Preference Flag -> fact_brand_survey[Brand Preference Flag]
- NPS Score -> fact_brand_survey[NPS Score]
- Region -> fact_brand_survey[Region]
- Segment -> fact_brand_survey[Segment]
- Date -> dim_date[Date]
