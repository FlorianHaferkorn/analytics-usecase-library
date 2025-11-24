# Market Share & Competitive Position - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_company_sales
  grain: market_segment_period
  primary_key:
  - MarketID
  - SegmentID
  - Date
  required_columns:
  - name: Company Sales Amount
    type: decimal
    role: amount
  - name: Date
    type: date
    role: date_key
  - name: Region
    type: string
    role: attribute
  - name: Segment
    type: string
    role: attribute
  - name: Category
    type: string
    role: attribute
- name: fact_market_size
  grain: market_segment_period
  primary_key:
  - MarketID
  - SegmentID
  - Date
  required_columns:
  - name: Total Market Sales Amount
    type: decimal
    role: amount
  - name: Main Competitor Sales Amount
    type: decimal
    role: amount
  - name: Date
    type: date
    role: date_key
  - name: Region
    type: string
    role: attribute
  - name: Segment
    type: string
    role: attribute
  - name: Category
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
- name: dim_market
  grain: market_segment
  primary_key:
  - MarketID
  required_columns:
  - name: Region
    type: string
  - name: Country
    type: string
  - name: Segment
    type: string
```

## 2. Semantic Model Requirements
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Required conform dimensions as per data contract.
- Relationships follow the structure listed above (single-direction many-to-one).
- Ensure role-playing dates/channel dimensions as needed for customer journeys.

## 3. Measures (DAX + Description)
Following KPIs need measures (DAX to be provided separately):
- Market Share % (Total) (ID: market.share.total.pct)
- Relative Market Share vs Main Competitor (ID: market.share.relative.pct)
- Revenue Growth % (ID: sales.revenue.growth_pct)

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
- Market_Share_Within_0_100
- Competitor_Data_Consistent

## 9. Model Mapping Reference
- Company Sales Amount -> fact_company_sales[Company Sales Amount]
- Total Market Sales Amount -> fact_market_size[Total Market Sales Amount]
- Main Competitor Sales Amount -> fact_market_size[Main Competitor Sales Amount]
- Date -> dim_date[Date]
