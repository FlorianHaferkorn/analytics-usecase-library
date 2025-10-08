---
id: "CST-001"
title: "Customer Retention & Churn Analysis"
domain: "Customer and Market"
owner: "Head of CRM / Marketing Analytics"
impact: "High"
status: "Draft"
last_update: "07.10.2025"
---

# Customer Retention & Churn Analysis

## 1. Business Goal
Increase customer lifetime value by identifying churn risks early, improving retention strategies, and quantifying the business impact of lost customers.

---

## 2. Business Context
Customer retention is more cost-efficient than acquisition.  
In most markets, 5–10 % of customer loss equals >20 % of profit erosion.  
This use case provides a standardized way to measure churn, detect behavioral signals of attrition, and prioritize high-value retention interventions based on profitability and engagement metrics.

---

## 3. Key Questions
- What is the current retention and churn rate?  
- Which segments show the highest churn risk?  
- What behaviors precede churn (e.g., declining frequency, basket size)?  
- Which actions or offers most effectively prevent churn?  
- How much incremental margin is gained per retained customer?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Retention % | Retained Customers ÷ Total Customers (prior period) | % | 1 decimal |
| Churn % | 1 − Retention % | % | 1 decimal |
| CLV (Customer Lifetime Value) | Σ (Gross Margin per period ÷ discount factor) | € | 0–2 decimals |
| Reactivation Rate % | Reactivated Customers ÷ Lost Customers | % | 1 decimal |
| At-Risk Share % | Customers flagged as churn-risk ÷ Active Base | % | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Customer ID, Segment, Region, Channel  
- Transaction Date, Net Sales Amount, Margin Amount  
- Last Purchase Date, Visit Frequency, Basket Size  
- Optional: Loyalty Tier, Campaign Interaction, Satisfaction Score (NPS)

---

## 6. Segmentation & Hierarchies
- Customer: Segment > Subsegment > Individual  
- Channel: Online / Offline / Partner  
- Region: Country > Region > City  
- Time: Year > Quarter > Month  
- Product: Category > Subcategory > SKU  

---

## 7. Scope & Assumptions
- Churn = No purchase activity within X months (configurable by business model).  
- Retention window typically 12 months rolling.  
- CLV discounted at 10 % WACC; currency EUR.  
- NPS and campaign data used as behavioral signals (if available).  
- One record per customer per month in aggregate dataset.

---

## 8. Data Freshness & Cadence
- Refresh frequency: weekly (Monday 06:00 CET).  
- Latency ≤ 7 days post-transaction.  
- Historical depth = 36 months.  
- Data Owner: CRM Analytics Team.

---

## 9. Edge Cases & QA Rules
- Customers with <2 transactions excluded from churn calculation (insufficient history).  
- Churn % must be within [0%; 100%].  
- Duplicated Customer IDs removed.  
- Referential integrity ≥ 99.9 % across Customer/Date.  
- CLV outliers (>99th percentile) capped in analysis.

---

## 10. Minimum Viable Dataset (MVD)
- Required: Customer ID, Date, Net Sales Amount, Margin Amount.  
- Optional: Channel, Segment, Last Purchase Date.  
- Extended: Campaign ID, NPS Score, Loyalty Tier, Visit Frequency.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Execute churn prevention campaign for at-risk customers | C1 | Churn ↓ 5–10 %; Retention ↑ |
| Introduce win-back campaigns for lost high-value customers | C2 | Reactivation +10–20 % |
| Personalize communication frequency by engagement score | D1 | Retention ↑; ROI on marketing spend ↑ |
| Link loyalty benefits to purchase frequency | SP1 | CLV +10–15 % |
| Automate churn alerts to account managers | O2 | Time-to-action ↓ 50 % |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| Retention | +3–5 pp Retention % | vs LY |
| Profitability | +5–10 % incremental margin | per retained customer |
| ROI | +15–25 % ROI on retention campaigns | vs prior quarter |

---

## 13. Related Processes
CRM Campaign Management · Loyalty Programs · Customer Segmentation · Marketing Automation.

---

## 14. Insights & Learnings
Most churn originates from declining engagement, not dissatisfaction.  
Predictive churn models are most effective when paired with campaign automation.  
Early detection (e.g., drop in frequency or spend) yields the highest ROI in retention spend.

---

## 15. Cross-References
- Related Use Cases:  
  `[CST-002 Product Lifecycle Performance](../03_Customer_and_Market/CST-002_Product_Lifecycle_Performance.md)`  
  `[COM-003 Promotion Effectiveness](../01_Commercial/COM-003_Promotion_Effectiveness.md)`  
  `[COR-004 Strategic KPI Dashboard](../04_Corporate_and_Strategy/COR-004_Strategic_KPI_Dashboard.md)`  
- Related Documents:  
  [`KPI Catalog`](../_includes/KPI_Catalog.md) · [`Action Codes`](../_includes/ActionCodes.md) · [`Glossary`](../_includes/Glossary.md)

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Name / Role] |
| Technical Reviewer | [Name / Role] |
| Version | v1.0 |
| Review Date | DD.MM.YYYY |
| Review Notes | [Summary of comments] |

---

_Last updated: 07.10.2025_
