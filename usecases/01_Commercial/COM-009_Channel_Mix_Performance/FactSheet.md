---
id: "COM-009"
title: "Channel Mix Performance"
domain: "Commercial"
owner: "Head of Sales / Head of Trade Marketing"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "margin.gm.pct"]
action_codes: ["M3", "P2", "D1"]
expected_impact: "Shift channel mix towards higher-margin and strategic channels while protecting top-line growth."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Channel",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "Channel_Share_100", "GM_By_Channel_Consistent"]
required_kpi_ids: [
  "sales.net_sales.amount",
  "sales.net_sales.channel_share.pct",
  "margin.gm.pct",
  "margin.gm.channel_contribution.amount"
]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  sales.net_sales.channel_share.pct: "Channel Revenue Share %"
  margin.gm.pct: "Gross Margin %"
  margin.gm.channel_contribution.amount: "Channel Contribution Margin Amount"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Gross Margin Amount", type: decimal, role: amount }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: Channel, type: string, role: channel }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Area, type: string }
        - { name: Store, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Gross Margin Amount": "fact_sales[Gross Margin Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
  "Channel": "fact_sales[Channel]"
---

# Channel Mix Performance

## 1. Business Goal
Understand and optimize the performance of different sales channels (e.g., retail, e-commerce, wholesale) by measuring their contribution to revenue and margin, and steering channel mix towards strategic and profitable channels.

---

## 2. Business Context
Companies increasingly sell through multiple channels with different cost structures and margin profiles.  
Without a structured view on channel mix and profitability, growth may shift into low-margin channels, eroding overall profitability.  
This Use Case provides a standardized channel mix view with revenue and margin KPIs for tactical steering.

---

## 3. Key Questions
- How is revenue and margin distributed across channels today, and how has the mix changed over time?
- Which channels deliver the highest contribution margin, and which ones dilute profitability?
- Are we overexposed to any single channel from a risk and dependency perspective?
- How do channel promotions and pricing strategies affect the mix?

---

## 4. Key KPIs
| KPI                        | Definition                                         | Unit | Format   |
|----------------------------|----------------------------------------------------|------|----------|
| Net Sales Amount           | Sum of net sales                                   | EUR  | € #,0.00 |
| Channel Revenue Share %    | Channel Net Sales / Total Net Sales                | %    | 1 decimal |
| Gross Margin %             | (Net Sales – COGS) / Net Sales                     | %    | 1 decimal |
| Channel Contribution Margin| Gross Margin allocated to channel                  | EUR  | € #,0.00 |

---

## 5. Required Attributes (Business-Level)
- Channel (retail, e-commerce, wholesale, etc.)
- Org (region/area/store)
- Product (category/subcategory/SKU)
- Net Sales Amount, Gross Margin Amount

---

## 6. Segmentation & Hierarchies
- Channel: Channel Group > Channel  
- Org: Region > Area > Store  
- Product: Category > Subcategory > SKU  
- Time: Year > Quarter > Month  

---

## 7. Scope & Assumptions
- Allocation of shared costs to channels is out of scope initially; analysis is at gross margin level.
- Returns and discounts are included in Net Sales.

---

## 8. Data Freshness & Cadence
- Data refresh: daily or weekly.
- Reporting cadence: weekly/monthly channel steering.

---

## 9. Edge Cases & QA Rules
- Channel must be populated for all sales lines (> 99.5 % coverage).
- Channel share across all channels should sum to ~100 % per period.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Sales fact with Net Sales Amount, Gross Margin Amount, Date, Org, Product, Channel.
- Optional:
  - Channel cost assumptions for deeper profitability analysis.

---

## 11. Typical Actions
| Action                                     | Code | Expected Effect                    |
|--------------------------------------------|------|------------------------------------|
| Shift promotions towards high-margin channels | M3 | Higher blended GM %                |
| Adjust trade terms in low-margin channels  | D1   | Margin dilution reduced            |
| Invest in digital channels with high GM %  | P2   | Growth in profitable channels      |

---

## 12. Expected Business Impact
| Dimension     | Expected Impact           | Measurement |
|---------------|---------------------------|-------------|
| Profitability | +0.5–1.0 pp Gross Margin %| vs prior year |
| Revenue       | +2–3 % Net Sales         | vs prior year |

---

## 13. Related Processes
Channel Strategy → Trade Terms Management → Promo Planning → Performance Review.

---

## 14. Insights & Learnings
Typical findings include over-dependence on specific channels, underused high-margin channels, and misaligned promo intensity vs channel profitability.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-001 Sales Performance vs Plan & LY](../COM-001_Sales_Performance/FactSheet.md)`  
  `[COM-002 Gross Margin % vs Plan & Last Year](../COM-002_Gross_Margin_Analysis/FactSheet.md)`  
  `[COM-005 Promotion ROI & Effectiveness](../COM-005_Promotion_ROI_and_Effectiveness/FactSheet.md)`  

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

