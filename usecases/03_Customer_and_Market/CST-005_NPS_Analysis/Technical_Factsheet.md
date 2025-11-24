# NPS Analysis - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_nps_survey
  grain: response
  primary_key:
  - ResponseID
  required_columns:
  - name: ResponseID
    type: string
    role: attribute
  - name: CustomerID
    type: string
    role: customer_key
  - name: ResponseDate
    type: date
    role: date_key
  - name: Channel
    type: string
    role: channel
  - name: Touchpoint
    type: string
    role: attribute
  - name: Score
    type: int
    role: attribute
  - name: Comment
    type: string
    role: attribute
- name: fact_customer_status
  grain: customer_month
  primary_key:
  - CustomerID
  - SnapshotMonth
  required_columns:
  - name: SnapshotMonth
    type: date
    role: date_key
  - name: Status
    type: string
    role: attribute
  - name: ChurnFlag
    type: bool
    role: indicator
dims:
- name: dim_customer
  grain: customer
  primary_key:
  - CustomerID
  required_columns:
  - name: Region
    type: string
  - name: Market
    type: string
  - name: Segment
    type: string
  - name: LoyaltyTier
    type: string
- name: dim_date
  grain: date
  primary_key:
  - Date
relationships:
- from: fact_nps_survey.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_nps_survey.ResponseDate
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_customer_status.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_customer_status.SnapshotMonth
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
```

## 2. Semantic Model Requirements
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Required conform dimensions as per data contract.
- Relationships follow the structure listed above (single-direction many-to-one).
- Ensure role-playing dates/channel dimensions as needed for customer journeys.

## 3. Measures (DAX + Description)
Following KPIs need measures (DAX to be provided separately):
- NPS Index (ID: crm.nps.index)
- Customer Retention % (ID: crm.retention.pct)
- Churn % (ID: crm.churn.pct)

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
- Responses_Sufficient
- Score_Within_11_11

## 9. Model Mapping Reference
- NPS Score -> fact_nps_survey[Score]
- NPS Comment -> fact_nps_survey[Comment]
- Customer -> dim_customer[CustomerID]
