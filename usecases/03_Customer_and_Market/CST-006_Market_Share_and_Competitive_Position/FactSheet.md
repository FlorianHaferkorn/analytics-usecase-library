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
expected_impact: "+0.5–1.0 pp market share in priority segments; more focused growth investments."
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

# Market Share & Competitive Position

## 1. Business Goal
Quantify market share and relative competitive position by region, segment, and category to steer growth investments and pricing strategy.

---

## 2. Business Context
Revenue growth in isolation is not sufficient if the overall market is growing faster.  
Without a consistent market share view, it is hard to see whether the company is winning or losing relative to competitors and where to focus commercial investments.  
This Use Case combines internal sales with external market data to provide a coherent picture of competitive position.

---

## 3. Key Questions
- What is our overall and segment-level market share, and how has it developed over time?
- In which regions, segments, or categories are we gaining or losing share?
- How do we compare to the main competitor in our priority segments (relative share)?
- Where should we invest in commercial resources, promotions, or innovation to gain share?

---

## 4. Key KPIs
| KPI                               | Definition                                              | Unit | Format    |
|-----------------------------------|---------------------------------------------------------|------|-----------|
| Market Share % (Total)           | Company Sales / Total Market Sales                      | %    | 1 decimal |
| Relative Market Share vs Main Competitor | Company Sales / Main Competitor Sales            | x    | 1 decimal |
| Revenue Growth %                  | YoY revenue growth vs last year                         | %    | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Region, Country, Segment
- Category, Subcategory
- Company Sales Amount, Total Market Sales Amount, Main Competitor Sales Amount

---

## 6. Segmentation & Hierarchies
- Market: Region > Country  
- Segment: Segment > Channel  
- Product: Category > Subcategory  
- Time: Year > Quarter > Month  

---

## 7. Scope & Assumptions
- Market data comes from trusted external sources (panel data, market research) with known refresh cycles.
- Company sales and market data share consistent definitions for region, category, and period.

---

## 8. Data Freshness & Cadence
- Market data refresh: monthly or quarterly (depending on provider).
- Company sales: monthly (aligned with financial close).

---

## 9. Edge Cases & QA Rules
- Regions or segments without market data are flagged and excluded from share calculations.
- Market share values must be between 0 % and 100 %; relative share may exceed 1.0 (e.g., highly dominant).

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Aggregated company sales by market segment and period.
  - Market size and competitor sales for the same segment and period.

---

## 11. Typical Actions
| Action                                            | Code | Expected Effect                    |
|---------------------------------------------------|------|------------------------------------|
| Focus investments on segments with share upside   | SP1  | Gain share in priority segments    |
| Defend strongholds where competition intensifies  | D1   | Protect share and profitability    |
| Adjust pricing/promo mix in weak positions        | P2   | Stabilize or grow share            |

---

## 12. Expected Business Impact
| Dimension | Expected Impact              | Measurement |
|-----------|------------------------------|-------------|
| Growth    | +0.5–1.0 pp market share    | vs prior year |
| Revenue   | +2–3 % Net Sales            | vs prior year |

---

## 13. Related Processes
Strategic Planning → Market & Competitive Intelligence → Channel & Segment Strategy → Commercial Execution.

---

## 14. Insights & Learnings
Typical findings include high growth but declining share in fast-growing markets, and pockets of underpenetration in strategic segments.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-001 Sales Performance vs Plan & LY](../../01_Commercial/COM-001_Sales_Performance/FactSheet.md)`  
  `[CST-002 Product Lifecycle Performance](../CST-002_Product_Lifecycle_Performance/FactSheet.md)`  

---

## 16. Review Information
| Field              | Value          |
|--------------------|----------------|
| Business Reviewer  | [Name / Role]  |
| Technical Reviewer | [Name / Role]  |
| Version            | v0.1           |
| Review Date        | DD.MM.YYYY     |
| Review Notes       | [Summary]      |

---

_Last updated: 19.11.2025_

