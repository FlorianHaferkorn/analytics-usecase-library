---
id: "CST-001"
title: "Customer Retention & Churn Analysis"
domain: "Customer and Market"
owner: "Head of CRM / Marketing Analytics"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Customer Retention %", "CLV %", "Revenue Growth %"]
supports_strategic_kpi_ids: ["crm.retention.pct", "crm.clv.amount", "sales.revenue.growth_pct"]
action_codes: ["C1", "C2", "D1", "SP1", "O2"]
expected_impact: "+3-5 pp Retention; +5-10 % incremental margin; +15-25 % ROI on retention campaigns"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Customer.Region>Market>Store",
  "Customer.Segment>LoyaltyTier",
  "Channel",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Customer Segment: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "Retention_Range", "Customer_Key_Unique"]
required_kpi_ids: [
  "crm.retention.pct",
  "crm.churn.pct",
  "crm.clv.amount",
  "crm.reactivation.pct",
  "crm.at_risk_share.pct"
]
required_kpis:
  crm.retention.pct: "Retention %"
  crm.churn.pct: "Churn %"
  crm.clv.amount: "CLV (Customer Lifetime Value)"
  crm.reactivation.pct: "Reactivation Rate %"
  crm.at_risk_share.pct: "At-Risk Share %"
data_requirements:
  facts:
    - name: fact_customer_transactions
      grain: customer_day
      primary_key: [CustomerID, Date]
      required_columns:
        - { name: CustomerID, type: string, role: customer_key }
        - { name: Date, type: date, role: date_key }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Margin Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Channel, type: string, role: channel }
    - name: fact_customer_profile
      grain: customer_month
      primary_key: [CustomerID, SnapshotMonth]
      required_columns:
        - { name: SnapshotMonth, type: date, role: date_key }
        - { name: Segment, type: string, role: segment }
        - { name: LoyaltyTier, type: string, role: attribute }
        - { name: "Last Purchase Date", type: date, role: helper }
        - { name: "Visit Frequency", type: decimal, role: helper }
        - { name: "Basket Size", type: decimal, role: helper }
        - { name: "Churn Flag", type: bool, role: indicator }
  dims:
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Region, type: string }
        - { name: Market, type: string }
        - { name: AcquisitionChannel, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_customer_transactions.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_transactions.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_customer_profile.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_profile.SnapshotMonth, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Customer ID": "dim_customer[CustomerID]"
  "Region": "dim_customer[Region]"
  "Market": "dim_customer[Market]"
  "Net Sales Amount": "fact_customer_transactions[Net Sales Amount]"
  "Margin Amount": "fact_customer_transactions[Margin Amount]"
  "Last Purchase Date": "fact_customer_profile[Last Purchase Date]"
  "Visit Frequency": "fact_customer_profile[Visit Frequency]"
  "Basket Size": "fact_customer_profile[Basket Size]"
  "Churn Flag": "fact_customer_profile[Churn Flag]"
  "Date": "dim_date[Date]"
---

# Customer Retention & Churn Analysis

## 1. Business Goal
Increase customer lifetime value by identifying churn risks early, improving retention strategies, and quantifying the business impact of lost customers.

---

## 2. Business Context
Marketing and Sales often debate whether declining revenue stems from acquisition issues or retention gaps. Legacy reporting treats churn as an annual KPI, making it impossible to intervene in time. This use case consolidates behavioral signals (frequency, recency, monetary value, engagement) to flag churn risk within days, link it to lost margin, and guide precise retention actions (campaigns, loyalty, sales outreach). It also proves ROI by attributing incremental value to retained or reactivated customers.

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
| Retention % | Customers active in both Period T and T-1 / Customers active in T-1 | % | 1 decimal |
| Churn % | 1 - Retention % | % | 1 decimal |
| CLV Amount | Discounted gross margin per customer over horizon | EUR | 0 decimals |
| Reactivation Rate % | Reactivated customers / Lost customers | % | 1 decimal |
| At-Risk Share % | Customers flagged at risk / Active customers | % | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Customer ID, Segment, Region, Channel
- Transaction Date, Net Sales Amount, Margin Amount
- Last Purchase Date, Visit Frequency, Basket Size
- Optional: Loyalty Tier, Campaign Interaction, Satisfaction Score (NPS)

---

## 6. Segmentation & Hierarchies
- Customer: Region > Market > Store/Account
- Segment: Value Tier > Loyalty Tier > Lifecycle Stage
- Channel: Direct / Indirect / Digital
- Time: Year > Quarter > Month > Week
- Product: Category > Subcategory (for churn drivers)

---

## 7. Scope & Assumptions
- Churn = No purchase activity within X months (configurable by business model).
- Retention window typically 12 months rolling.
- CLV discounted at 10 % WACC; currency EUR.
- NPS and campaign data used as behavioral signals (if available).
- One record per customer per month in aggregate dataset.

---

## 8. Data Freshness & Cadence
- Transactions refresh daily; churn scoring runs nightly.
- Engagement/loyalty data ingested within 24h of event.
- Historical depth: 36 months for cohort analysis.
- Data Owner: CRM Analytics; Technical Owner: Customer Data Platform team.

---

## 9. Edge Cases & QA Rules
- Customers with <2 transactions excluded from churn calculation (insufficient history).
- Churn % must be within [0%; 100%].
- Duplicated Customer IDs removed.
- Referential integrity >= 99.9 % across Customer/Date.
- CLV outliers (>99th percentile) capped in analysis.

---

## 10. Minimum Viable Dataset (MVD)
- Required: Customer ID, transaction history (Date, Amount), classification (segment, region).
- Optional: Loyalty tier, engagement scores, campaign history.
- Extended: Digital behavior (web/app), service tickets, satisfaction survey data.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Execute churn prevention campaign for at-risk customers | C1 | Churn -5-10 %; Retention improves |
| Introduce win-back campaigns for lost high-value customers | C2 | Reactivation +10-20 % |
| Personalize communication frequency by engagement score | D1 | Retention improves; ROI on marketing spend improves |
| Link loyalty benefits to purchase frequency | SP1 | CLV +10-15 % |
| Automate churn alerts to account managers | O2 | Time-to-action reduces 50 % |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Retention | +3-5 pp retention rate | vs Prior Quarter |
| Margin | +5-10 % incremental gross margin | vs baseline |
| Campaign ROI | +15-25 % ROI on retention programs | post-campaign review |

---

## 13. Related Processes
CRM Campaign Management -> Loyalty Programs -> Customer Segmentation -> Marketing Automation.

---

## 14. Insights & Learnings
Churn risk typically increases 4-6 weeks before the last purchase, visible through declining frequency and lower basket value. Retention campaigns perform best when triggered by behavior (recency/frequency) rather than demographics alone.

---

## 15. Cross-References
- Related Use Cases:  
  `[CST-002 Product Lifecycle Performance](../CST-002_Product_Lifecycle_Performance/FactSheet.md)`  
  `[COM-003 Promotion Effectiveness](../../01_Commercial/COM-003_Promotion_Effectiveness/FactSheet.md)`  
  `[COR-004 Strategic KPI Dashboard](../../04_Corporate_and_Strategy/COR-004_Strategic_KPI_Dashboard/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

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

_Last updated: 04.11.2025_
