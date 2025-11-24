# Campaign Effectiveness - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_campaign
  grain: campaign_customer
  primary_key:
  - CampaignID
  - CustomerID
  required_columns:
  - name: CampaignID
    type: string
    role: campaign_key
  - name: CustomerID
    type: string
    role: customer_key
  - name: Channel
    type: string
    role: channel
  - name: SpendAmount
    type: decimal
    role: amount
  - name: ResponseFlag
    type: bool
    role: indicator
  - name: ConversionFlag
    type: bool
    role: indicator
  - name: RevenueAmount
    type: decimal
    role: amount
dims:
- name: dim_campaign
  grain: campaign
  primary_key:
  - CampaignID
  required_columns:
  - name: CampaignName
    type: string
  - name: CampaignType
    type: string
  - name: StartDate
    type: date
  - name: EndDate
    type: date
- name: dim_customer
  grain: customer
  primary_key:
  - CustomerID
  required_columns:
  - name: Segment
    type: string
  - name: LoyaltyTier
    type: string
- name: dim_date
  grain: date
  primary_key:
  - Date
relationships:
- from: fact_campaign.CampaignID
  to: dim_campaign.CampaignID
  cardinality: many-to-one
  direction: single
- from: fact_campaign.CustomerID
  to: dim_customer.CustomerID
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
- Campaign ROI % (ID: sales.promo.roi.pct)
- Uplift % vs. Baseline (ID: sales.promo.uplift_pct)
- Reactivation Rate % (ID: crm.reactivation.pct)
- At-Risk Share % (ID: crm.at_risk_share.pct)
- Retention % (ID: crm.retention.pct)

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
- ROI_Within_Range
- Spend_Reconciles

## 9. Model Mapping Reference
- Campaign -> dim_campaign[CampaignID]
- Customer -> dim_customer[CustomerID]
- Campaign Spend -> fact_campaign[SpendAmount]
- Campaign Revenue -> fact_campaign[RevenueAmount]
