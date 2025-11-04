---
id: "CST-001"
title: "Customer Retention & Churn Analysis"
domain: "Customer and Market"
owner: "Head of CRM / Marketing Analytics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Customer Retention %", "CLV %", "Revenue Growth %"]
action_codes: ["C1", "C2", "D1", "SP1", "O2"]
expected_impact: "+3-5 pp Retention; +5-10 % incremental margin; +15-25 % ROI on retention campaigns"
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
---

# Customer Retention & Churn Analysis

## 1. Business Goal
Increase customer lifetime value by identifying churn risks early, improving retention strategies, and quantifying the business impact of lost customers.

---
id: "CST-001"
title: "Customer Retention & Churn Analysis"
domain: "Customer and Market"
owner: "Head of CRM / Marketing Analytics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Customer Retention %", "CLV %", "Revenue Growth %"]
action_codes: ["C1", "C2", "D1", "SP1", "O2"]
expected_impact: "+3-5 pp Retention; +5-10 % incremental margin; +15-25 % ROI on retention campaigns"
required_kpi_ids: []
required_kpis: {}
---

## 3. Key Questions
- What is the current retention and churn rate?  
- Which segments show the highest churn risk?  
- What behaviors precede churn (e.g., declining frequency, basket size)?  
- Which actions or offers most effectively prevent churn?  
- How much incremental margin is gained per retained customer?

---
id: "CST-001"
title: "Customer Retention & Churn Analysis"
domain: "Customer and Market"
owner: "Head of CRM / Marketing Analytics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Customer Retention %", "CLV %", "Revenue Growth %"]
action_codes: ["C1", "C2", "D1", "SP1", "O2"]
expected_impact: "+3-5 pp Retention; +5-10 % incremental margin; +15-25 % ROI on retention campaigns"
required_kpi_ids: []
required_kpis: {}
---

## 5. Required Attributes (Business-Level)
- Customer ID, Segment, Region, Channel  
- Transaction Date, Net Sales Amount, Margin Amount  
- Last Purchase Date, Visit Frequency, Basket Size  
- Optional: Loyalty Tier, Campaign Interaction, Satisfaction Score (NPS)

---
id: "CST-001"
title: "Customer Retention & Churn Analysis"
domain: "Customer and Market"
owner: "Head of CRM / Marketing Analytics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Customer Retention %", "CLV %", "Revenue Growth %"]
action_codes: ["C1", "C2", "D1", "SP1", "O2"]
expected_impact: "+3-5 pp Retention; +5-10 % incremental margin; +15-25 % ROI on retention campaigns"
required_kpi_ids: []
required_kpis: {}
---

## 7. Scope & Assumptions
- Churn = No purchase activity within X months (configurable by business model).  
- Retention window typically 12 months rolling.  
- CLV discounted at 10 % WACC; currency EUR.  
- NPS and campaign data used as behavioral signals (if available).  
- One record per customer per month in aggregate dataset.

---
id: "CST-001"
title: "Customer Retention & Churn Analysis"
domain: "Customer and Market"
owner: "Head of CRM / Marketing Analytics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Customer Retention %", "CLV %", "Revenue Growth %"]
action_codes: ["C1", "C2", "D1", "SP1", "O2"]
expected_impact: "+3-5 pp Retention; +5-10 % incremental margin; +15-25 % ROI on retention campaigns"
required_kpi_ids: []
required_kpis: {}
---

## 9. Edge Cases & QA Rules
- Customers with <2 transactions excluded from churn calculation (insufficient history).  
- Churn % must be within [0%; 100%].  
- Duplicated Customer IDs removed.  
- Referential integrity >= 99.9 % across Customer/Date.  
- CLV outliers (>99th percentile) capped in analysis.

---
id: "CST-001"
title: "Customer Retention & Churn Analysis"
domain: "Customer and Market"
owner: "Head of CRM / Marketing Analytics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Customer Retention %", "CLV %", "Revenue Growth %"]
action_codes: ["C1", "C2", "D1", "SP1", "O2"]
expected_impact: "+3-5 pp Retention; +5-10 % incremental margin; +15-25 % ROI on retention campaigns"
required_kpi_ids: []
required_kpis: {}
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
id: "CST-001"
title: "Customer Retention & Churn Analysis"
domain: "Customer and Market"
owner: "Head of CRM / Marketing Analytics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Customer Retention %", "CLV %", "Revenue Growth %"]
action_codes: ["C1", "C2", "D1", "SP1", "O2"]
expected_impact: "+3-5 pp Retention; +5-10 % incremental margin; +15-25 % ROI on retention campaigns"
required_kpi_ids: []
required_kpis: {}
---

## 13. Related Processes
CRM Campaign Management -> Loyalty Programs -> Customer Segmentation -> Marketing Automation.

---
id: "CST-001"
title: "Customer Retention & Churn Analysis"
domain: "Customer and Market"
owner: "Head of CRM / Marketing Analytics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Customer Retention %", "CLV %", "Revenue Growth %"]
action_codes: ["C1", "C2", "D1", "SP1", "O2"]
expected_impact: "+3-5 pp Retention; +5-10 % incremental margin; +15-25 % ROI on retention campaigns"
required_kpi_ids: []
required_kpis: {}
---

## 15. Cross-References
- Related Use Cases:  
  `[CST-002 Product Lifecycle Performance](../CST-002_Product_Lifecycle_Performance/FactSheet.md)`  
  `[COM-003 Promotion Effectiveness](../../01_Commercial/COM-003_Promotion_Effectiveness/FactSheet.md)`  
  `[COR-004 Strategic KPI Dashboard](../../04_Corporate_and_Strategy/COR-004_Strategic_KPI_Dashboard/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

---
id: "CST-001"
title: "Customer Retention & Churn Analysis"
domain: "Customer and Market"
owner: "Head of CRM / Marketing Analytics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Customer Retention %", "CLV %", "Revenue Growth %"]
action_codes: ["C1", "C2", "D1", "SP1", "O2"]
expected_impact: "+3-5 pp Retention; +5-10 % incremental margin; +15-25 % ROI on retention campaigns"
required_kpi_ids: []
required_kpis: {}
---

_Last updated: 03.11.2025_

