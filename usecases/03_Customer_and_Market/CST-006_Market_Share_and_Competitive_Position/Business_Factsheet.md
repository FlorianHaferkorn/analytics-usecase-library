---
id: "CST-006"
title: "Market Share & Competitive Position"
domain: "Customer and Market"
owner: "Head of Marketing / Strategy"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Strategic"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Revenue Growth %", "Market Share %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "market.share.total.pct"]
action_codes: ["SP1", "P2", "D1"]
expected_impact: "+0.5â€“1.0 pp market share in priority segments; more focused growth investments."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Market.Region>Country",
  "Customer.Segment>Channel",
  "Product.Category>Subcategory",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Region: All",
  "Segment: All"
]
qa_asserts: ["RI_OK", "Market_Share_Within_0_100", "Competitor_Data_Consistent"]
required_kpi_ids: [
  "market.share.total.pct",
  "market.share.relative.pct",
  "sales.revenue.growth_pct"
]
required_kpis:
  market.share.total.pct: "Market Share % (Total)"
  market.share.relative.pct: "Relative Market Share vs Main Competitor"
  sales.revenue.growth_pct: "Revenue Growth %"
data_requirements:
  facts:
    - name: fact_company_sales
      grain: market_segment_period
      primary_key: [MarketID, SegmentID, Date]
      required_columns:
        - { name: "Company Sales Amount", type: decimal, role: amount }
        - { name: Date, type: date, role: date_key }
        - { name: Region, type: string, role: attribute }
        - { name: Segment, type: string, role: attribute }
        - { name: Category, type: string, role: attribute }
    - name: fact_market_size
      grain: market_segment_period
      primary_key: [MarketID, SegmentID, Date]
      required_columns:
        - { name: "Total Market Sales Amount", type: decimal, role: amount }
        - { name: "Main Competitor Sales Amount", type: decimal, role: amount }
        - { name: Date, type: date, role: date_key }
        - { name: Region, type: string, role: attribute }
        - { name: Segment, type: string, role: attribute }
        - { name: Category, type: string, role: attribute }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
    - name: dim_market
      grain: market_segment
      primary_key: [MarketID]
      required_columns:
        - { name: Region, type: string }
        - { name: Country, type: string }
        - { name: Segment, type: string }
model_mapping:
  "Company Sales Amount": "fact_company_sales[Company Sales Amount]"
  "Total Market Sales Amount": "fact_market_size[Total Market Sales Amount]"
  "Main Competitor Sales Amount": "fact_market_size[Main Competitor Sales Amount]"
  "Date": "dim_date[Date]"
---

# Market Share & Competitive Position - Business Factsheet

## 1. Summary
- **Business Goal:** Quantify market share and relative competitive position by region, segment, and category to steer growth investments and pricing strategy.

---
- **Target Audience:** Head of Marketing / Strategy
- **Business Priority:** High
- **Expected Impact:** +0.5"1.0 pp market share in priority segments; more focused growth investments.

## 2. Core Questions
- What is our overall and segment-level market share, and how has it developed over time?
- In which regions, segments, or categories are we gaining or losing share?
- How do we compare to the main competitor in our priority segments (relative share)?
- Where should we invest in commercial resources, promotions, or innovation to gain share?
---

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| n/a | n/a | n/a | n/a |

## 4. Business Logic & Thresholds
- n/a

## 5. Action Codes (Business Perspective)
TODO: add action table.

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Market Share % (Total), Relative Market Share vs Main Competitor, Revenue Growth % with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Customer drill-down.
- Drill-through to transactional detail (orders/invoices).
- Export-ready table including action status.

## 7. Dependencies & Constraints
- n/a

## 8. Success Criteria
- n/a