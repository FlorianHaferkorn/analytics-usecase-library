> Status: Archived  
> Reason: Content consolidated into `docs/company/company_strategy.md`.  
> This document is kept for historical reference only and must not be used as a primary source.

# Strategic Alignment Map (Full Version)
_Version 2.0 | Last updated: 12.10.2025_

---

## Purpose
The **Strategic Alignment Map (Full Version)** connects all **Strategic KPIs (8)** with every **Analytics Use Case (29)**, including primary and secondary influence relationships, business ownership, impact intensity, and governance details.

This map represents the **top-down governance view** of the Analytics Framework — linking business strategy, analytical design, and operational action.

---

## 1. Alignment Overview (Condensed)

| Strategic KPI | Dimension | #Linked UCs | Primary Links | Secondary Links | Owner | Review |
|----------------|------------|-------------|----------------|------------------|--------|---------|
| Revenue Growth % | Growth | 6 | COM-001, COM-004, COM-002 | COM-003, COM-005, CST-003 | Head of Sales | Quarterly |
| Gross Margin % | Profitability | 6 | COM-002, COM-004, COM-003 | COM-001, COM-005, CST-003 | Head of Controlling | Quarterly |
| Working Capital % | Liquidity | 3 | COR-001 | COR-002, OPS-004 | Head of Treasury | Quarterly |
| OEE % | Efficiency | 5 | OPS-001, OPS-002 | OPS-003, OPS-004, OPS-005 | Head of Operations | Quarterly |
| Customer Retention % | Customer Value | 5 | CST-001, CST-002 | CST-003, CST-004, CST-005 | Head of Marketing | Quarterly |
| Carbon Emission Intensity | ESG | 2 | ESG-001 | ESG-002 | Head of Sustainability | Semi-Annual |
| Data Quality % | Governance | 4 | GOV-001, GOV-004 | GOV-002, GOV-003 | Chief Data Officer | Monthly |
| Innovation Rate % | Innovation & People | 4 | INN-001, HR-001 | INN-002, HR-002 | Head of HR | Quarterly |

---

## 2. Detailed Mapping by Strategic KPI

### 2.1 Revenue Growth %
```yaml
strategic_kpi: "Revenue Growth %"
dimension: "Growth"
primary_use_cases:
  - id: "COM-001"
    title: "Sales Performance vs Plan & LY"
    impact_intensity: "High"
    action_codes: ["P1 Tighten Prices", "P2 Discount Discipline"]
    expected_impact: "+3–5 pp Revenue Growth %, +1 pp GM %"
  - id: "COM-004"
    title: "Price Realization & Discount Discipline"
    impact_intensity: "High"
    action_codes: ["P1 List Price Management", "P2 Pricing Control"]
    expected_impact: "+1–2 pp Revenue Growth %, +0.5 pp GM %"
  - id: "COM-002"
    title: "Gross Margin Analysis"
    impact_intensity: "Medium"
    action_codes: ["P2 Tighten Discounts", "PC2 Supplier Negotiation"]
    expected_impact: "+0.5 pp Revenue Growth % (via GM effect)"
secondary_use_cases:
  - COM-003 Product Mix & Contribution
  - COM-005 Promotion ROI & Effectiveness
  - CST-003 Customer Lifetime Value
governance_owner: "Head of Sales"
review_cycle: "quarterly"
completeness_score: 0.97
```

### 2.2 Gross Margin %
```yaml
strategic_kpi: "Gross Margin %"
dimension: "Profitability"
primary_use_cases:
  - COM-002 Gross Margin Analysis
  - COM-004 Price Realization & Discount Discipline
  - COM-003 Product Mix & Contribution
secondary_use_cases:
  - COM-001 Sales Performance
  - COM-005 Promotion ROI
  - CST-003 CLV Analysis
impact_intensity:
  COM-002: High
  COM-004: High
  COM-003: Medium
expected_impact: "+0.5–1 pp GM %, −2 % COGS"
governance_owner: "Head of Controlling"
review_cycle: "quarterly"
completeness_score: 0.96
```

### 2.3 Working Capital %
```yaml
strategic_kpi: "Working Capital %"
dimension: "Liquidity"
primary_use_cases:
  - COR-001 Working Capital & CCC
secondary_use_cases:
  - COR-002 Cash Flow Forecast Accuracy
  - OPS-004 Supply Chain Reliability
impact_intensity:
  COR-001: High
  COR-002: Medium
expected_impact: "−5 days CCC, +2 % Cash Conversion"
governance_owner: "Head of Treasury"
review_cycle: "quarterly"
completeness_score: 0.97
```

### 2.4 OEE %
```yaml
strategic_kpi: "Overall Equipment Effectiveness (OEE) %"
dimension: "Efficiency"
primary_use_cases:
  - OPS-001 OEE & Throughput
  - OPS-002 Downtime Root Cause
secondary_use_cases:
  - OPS-003 Production Yield & Scrap Rate
  - OPS-004 Supply Chain Reliability
  - OPS-005 Capacity Utilization
impact_intensity:
  OPS-001: High
  OPS-002: High
  OPS-003: Medium
expected_impact: "+5 pp OEE %, −3 % Production Cost"
governance_owner: "Head of Operations"
review_cycle: "quarterly"
completeness_score: 0.98
```

### 2.5 Customer Retention %
```yaml
strategic_kpi: "Customer Retention %"
dimension: "Customer Value"
primary_use_cases:
  - CST-001 Customer Retention Analysis
  - CST-002 Churn Prediction
secondary_use_cases:
  - CST-003 CLV Analysis
  - CST-004 Campaign Effectiveness
  - CST-005 NPS Analysis
impact_intensity:
  CST-001: High
  CST-002: High
  CST-003: Medium
expected_impact: "+2–3 pp Retention, +3 pp NPS"
governance_owner: "Head of Marketing"
review_cycle: "quarterly"
completeness_score: 0.95
```

### 2.6 Carbon Emission Intensity (tCO₂e/€)
```yaml
strategic_kpi: "Carbon Emission Intensity (tCO₂e/€)"
dimension: "ESG"
primary_use_cases:
  - ESG-001 Emission Tracking & Reporting
secondary_use_cases:
  - ESG-002 Energy Efficiency Optimization
impact_intensity:
  ESG-001: High
  ESG-002: Medium
expected_impact: "−10 % CO₂ Intensity YoY, −5 % Energy Cost"
governance_owner: "Head of Sustainability"
review_cycle: "semi-annual"
completeness_score: 0.96
```

### 2.7 Data Quality %
```yaml
strategic_kpi: "Data Quality %"
dimension: "Governance"
primary_use_cases:
  - GOV-001 Data Quality Monitoring
  - GOV-004 Audit Findings Management
secondary_use_cases:
  - GOV-002 Access & Compliance Review
  - GOV-003 Risk & Control Testing
impact_intensity:
  GOV-001: High
  GOV-004: Medium
expected_impact: "+2 pp DQ %, −20 % Issues"
governance_owner: "Chief Data Officer"
review_cycle: "monthly"
completeness_score: 0.99
```

### 2.8 Innovation Rate %
```yaml
strategic_kpi: "Innovation Rate %"
dimension: "Innovation & People"
primary_use_cases:
  - INN-001 Innovation Pipeline Performance
  - HR-001 Employee Development & Learning
secondary_use_cases:
  - INN-002 Digital Adoption Index
  - HR-002 Workforce Productivity
impact_intensity:
  INN-001: High
  HR-001: Medium
expected_impact: "+1 pp Innovation Rate, +0.5 pp Productivity"
governance_owner: "Head of HR"
review_cycle: "quarterly"
completeness_score: 0.96
```

---

## 3. Cross-Impact Matrix (Multi-KPI Influence)

| Use Case | Primary KPI | Secondary KPI(s) | Impact Intensity | Action Codes |
|-----------|--------------|------------------|------------------|---------------|
| COM-001 Sales Performance | Revenue Growth % | Gross Margin % | High | P1, P2 |
| COM-002 Gross Margin | Gross Margin % | Revenue Growth % | High | P2, PC2 |
| COM-003 Product Mix | Gross Margin % | Revenue Growth % | Medium | P3, M3 |
| COM-004 Price Realization | Revenue Growth % | Gross Margin % | High | P1, P2 |
| COM-005 Promotion ROI | Gross Margin % | Revenue Growth % | Medium | D1, D2 |
| COM-006 Customer Profitability | Gross Margin % | CLV % | Medium | P2, M3 |
| COR-001 Working Capital | Working Capital % | Cash Flow Accuracy % | High | W1, I1 |
| COR-002 Cash Flow Forecast | Working Capital % | Governance Score % | Medium | W2, F1 |
| COR-004 Strategic KPI Dashboard | Gross Margin %, Revenue Growth % | Cash Conversion Cycle, ESG-Aligned Revenue %, Turnover Rate %, Project ROI % | High | SP2, O2, SP1, O3, SP3 |
| OPS-001 OEE & Throughput | OEE % | Unit Cost % | High | M1, Q1 |
| OPS-002 Downtime RCA | OEE % | Availability % | High | M1, L1 |
| OPS-003 Production Yield | OEE % | Waste % | Medium | Q1, Q2 |
| OPS-004 Supply Chain Reliability | OEE % | Working Capital % | Medium | S1, L1 |
| OPS-005 Capacity Utilization | OEE % | Productivity % | Medium | M2, L2 |
| CST-001 Retention | Customer Retention % | NPS % | High | D1, M3 |
| CST-002 Churn Prediction | Customer Retention % | CLV % | High | D1, M3 |
| CST-003 CLV Analysis | CLV % | Gross Margin %, Retention % | Medium | M3, P2 |
| CST-004 Campaign Effectiveness | Marketing ROI % | Retention % | Medium | D2, M3 |
| CST-005 NPS Analysis | NPS % | Retention % | Medium | D3, M3 |
| ESG-001 Emission Tracking | Carbon Intensity % | Energy Efficiency % | High | E1, S1 |
| ESG-002 Energy Efficiency | Energy Efficiency % | Carbon Intensity % | Medium | S1, M1 |
| GOV-001 DQ Monitoring | Data Quality % | Governance Score % | High | G1, G2 |
| GOV-002 Access Review | Governance Score % | Data Quality % | Medium | G3, G4 |
| GOV-003 Risk Testing | Governance Score % | Data Quality % | Medium | G5 |
| GOV-004 Audit Findings | Data Quality % | Governance Score % | Medium | G2, G5 |
| INN-001 Innovation Pipeline | Innovation Rate % | New Product Revenue % | High | I2 |
| INN-002 Digital Adoption | Innovation Rate % | Productivity % | Medium | I3 |
| HR-001 Employee Learning | Innovation Rate % | Productivity % | Medium | H1, H2 |
| HR-002 Workforce Productivity | Productivity % | Engagement % | Medium | H3, H4 |

---

## 4. Governance Summary

| Metric | Value |
|--------|--------|
| **Strategic KPIs Covered** | 8 |
| **Total Use Cases Linked** | 29 |
| **Average Completeness Score** | 0.97 |
| **Cross-Linked KPIs (Secondary)** | 21 |
| **Copilot Ready** | Yes |
| **Maintainers** | analytics-core-team |
| **Contact** | analytics-governance@company.com |



