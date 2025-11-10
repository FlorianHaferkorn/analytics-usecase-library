# Action Codes

This file defines standardized operational levers ("Actions") used across all analytical Use Cases.  
Each Action Code describes **what to do** when a KPI deviation is detected and **which KPI(s)** it affects.  
It serves as the semantic bridge between analysis and business execution.


---

## 1. Purpose
- Create a consistent action taxonomy across clusters (Commercial, Operational, Customer, Corporate).  
- Enable automation (Copilot, Power Automate, or AI triggers) via code-based linking.  
- Support impact tracking and cross-functional accountability.  

Each Action Code is uniquely identified and classified by:
- **Impact Dimension:** which strategic goal it supports (e.g., Profitability, Efficiency).  
- **Primary KPI:** which KPI(s) it primarily influences.  
- **Example Use Cases:** where this action typically applies.  
- **Expected Effect:** quantitative or directional impact on KPIs.


---

## 2. Structure

| Field | Description |
|--------|--------------|
| **Code** | Unique Action Code (2–3 characters + numeric). |
| **Name** | Short, action-oriented description. |
| **Impact Dimension** | Growth, Profitability, Liquidity, Efficiency, Customer Value, ESG, Governance, or Innovation & People. |
| **Target KPI** | Strategic KPI(s) primarily affected. |
| **Typical Use Cases** | Related Use Case IDs or examples. |
| **Expected Effect** | Measurable or directional impact. |
| **Trigger Condition** | Threshold or pattern that typically activates this action. |

---

## 3. Action Code Library

### **Growth**
| Code | Action | Impact Dimension | Target KPI | Typical Use Cases | Expected Effect | Trigger Condition |
|------|---------|------------------|-------------|-------------------|-----------------|-------------------|
| **G1** | Launch New Product | Growth | Innovation Revenue %, Revenue Growth % | COM-007 Innovation Effectiveness | +5 % new revenue | Δ% Revenue < Plan −2 % |
| **G2** | Expand Market Coverage | Growth | Market Share %, Revenue Growth % | CST-003 Market Dynamics | +0.5 pp market share | Market Share stagnant ≥ 3M |
| **G3** | Channel Expansion | Growth | Revenue Growth %, Customer Count | COM-001 Sales Performance | +3–5 % revenue | Growth slowdown vs LY |
| **G4** | Bundle Products | Growth | AOV, Cross-Sell Ratio % | CST-007 Cross-Sell | +3 % AOV | Low AOV (< Plan −5 %) |
| **G5** | Promo Calendar Optimization | Growth | Volume Growth %, Revenue Growth % | COM-003 Promotion Analysis | +2 % volume | Promo ROI < target 1.0 |
| **G6** | Plan Re-baseline | Growth | Revenue Growth %, Forecast Accuracy % | COM-006 Forecast Accuracy | +5 % accuracy | Forecast deviation > 10 % |
| **G7** | Demand Reforecast | Growth | Forecast Accuracy %, Revenue Growth % | COM-006 Forecast Accuracy | +5–10 % accuracy | Volume deviation > 5 % |
| **G8** | Price Elasticity Review | Growth | Price Realization %, Revenue Growth % | COM-002 Price Control | +1 % price efficiency | Elasticity drift > threshold |

---

### **Profitability**
| Code | Action | Impact Dimension | Target KPI | Typical Use Cases | Expected Effect | Trigger Condition |
|------|---------|------------------|-------------|-------------------|-----------------|-------------------|
| **P1** | Price Increase | Profitability | Gross Margin %, Price Realization % | COM-002 Price Control | +1–2 pp GM% | Price leakage > 3 % |
| **P2** | Tighten Discounts | Profitability | Discount Rate %, Gross Margin % | COM-004 Discount Effectiveness | +1 pp GM% | Discount share > 10 % |
| **P3** | Product Mix Steering | Profitability | Product Mix %, Gross Margin % | COM-004 Mix Analysis | +1 pp GM% | Low-margin mix > 60 % |
| **P4** | COGS Optimization | Profitability | COGS % of Sales, GM% | OPS-001 Cost Efficiency | −1 pp cost ratio | COGS rising > revenue |
| **P5** | SG&A Reduction | Profitability | Operating Cost Ratio % | COR-004 P&L Overview | −2 pp OpEx % | OpEx > Plan +5 % |
| **P6** | Margin Reforecast | Profitability | Gross Margin %, EBITDA Margin % | COR-004 Margin Review | +2 % forecast accuracy | Margin deviation > 2 pp |
| **P7** | Expense Freeze | Profitability | OpEx %, EBITDA Margin % | COR-004 Financial Overview | −1 % OpEx | OpEx trend +10 % vs LY |

---

### **Liquidity**
| Code | Action | Impact Dimension | Target KPI | Typical Use Cases | Expected Effect | Trigger Condition |
|------|---------|------------------|-------------|-------------------|-----------------|-------------------|
| **L1** | Accelerate Collections | Liquidity | DSO, Cash Conversion Cycle | COR-001 Working Capital | −5 days DSO | DSO > target +10 % |
| **L2** | Delay Supplier Payments | Liquidity | DPO, Working Capital % | COR-001 Working Capital | +3 days DPO | DPO < peer average |
| **L3** | Reduce Inventory | Liquidity | DIO, Working Capital % | OPS-007 Inventory Dynamics | −5–10 days DIO | Slow-moving stock > 10 % |
| **L4** | Optimize CapEx Plan | Liquidity | CapEx Ratio %, Free Cash Flow | COR-007 Investment Tracking | +5 % FCF | CapEx > budget +10 % |
| **L5** | Short-Term Financing | Liquidity | Cash Conversion Cycle | COR-003 Cash Flow Management | +10 % liquidity buffer | Cash < 30-day threshold |

---

### **Efficiency**
| Code | Action | Impact Dimension | Target KPI | Typical Use Cases | Expected Effect | Trigger Condition |
|------|---------|------------------|-------------|-------------------|-----------------|-------------------|
| **E1** | Streamline Processes | Efficiency | Cost per Unit, OEE | OPS-001 Process Analysis | −2–3 % unit cost | Cycle time â†‘ 10 % |
| **E2** | Increase Automation | Efficiency | Digital Process Share %, Labor Productivity % | COR-019 Digitalization | +10 % automation | Manual share > 50 % |
| **E3** | Supplier Consolidation | Efficiency | Supplier On-Time %, Cost per Unit | OPS-010 Procurement Optimization | +2 % OTD | ≥ 5 small suppliers/category |
| **E4** | Workforce Optimization | Efficiency | Labor Productivity %, Headcount Efficiency % | COR-008 Workforce Efficiency | +3–5 % productivity | Labor cost > Plan +5 % |
| **E5** | Maintenance Scheduling | Efficiency | OEE, Cost per Unit | OPS-004 Maintenance Planning | +2 % OEE | Downtime > threshold 5 % |
| **E6** | Lean Process Optimization | Efficiency | Cost per Unit, OEE | OPS-005 Process Optimization | −3 % cost/unit | Waste ratio > 5 % |
| **E7** | Supplier Collaboration | Efficiency | Lead Time, Supplier On-Time % | OPS-010 Supplier Reliability | −10 % lead time | Long delivery delay |
| **E8** | Inventory Policy Revision | Efficiency | DIO, Stockout Rate % | OPS-007 Inventory Dynamics | −5 days DIO | High stockouts or slow turns |
| **E9** | Throughput Balancing | Efficiency | OEE, Capacity Utilization % | OPS-004 Capacity Planning | +3 % throughput | Utilization < 80 % |

---

### **Customer Value**
| Code | Action | Impact Dimension | Target KPI | Typical Use Cases | Expected Effect | Trigger Condition |
|------|---------|------------------|-------------|-------------------|-----------------|-------------------|
| **C1** | Retention Campaign | Customer Value | Retention %, CLV | CST-001 Retention Analysis | +3–5 pp retention | Churn > 10 % |
| **C2** | Loyalty Program Optimization | Customer Value | NPS, Repeat Purchase Rate % | CST-002 Loyalty Effectiveness | +3 pts NPS | NPS drop > 5 pts |
| **C3** | Complaint Management | Customer Value | Complaint Rate %, NPS | CST-008 Service Quality | −0.3 pp complaints | Complaints rising > 20 % |
| **C4** | Cross-Selling | Customer Value | AOV, CLV | CST-007 Cross-Sell | +5 % AOV | Basket size < Plan −5 % |
| **C5** | Customer Win-Back Campaign | Customer Value | Retention %, CLV | CST-001 Churn Analysis | +2 pp retention | Inactive customer ratio > 15 % |
| **C6** | Pricing Personalization | Customer Value | AOV, NPS | CST-007 Segmented Pricing | +2–3 % sales | High churn risk segment |
| **C7** | Promotion ROI Review | Customer Value | Promo ROI %, Revenue Growth % | COM-003 Promotion Analysis | +10 % ROI | ROI < 0.9 |
| **C8** | Channel Incentive Program | Customer Value | Channel Sales %, Revenue Growth % | COM-001 Channel Management | +3–5 % sales | Channel below target |

---

### **ESG**
| Code | Action | Impact Dimension | Target KPI | Typical Use Cases | Expected Effect | Trigger Condition |
|------|---------|------------------|-------------|-------------------|-----------------|-------------------|
| **S1** | Reduce COâ‚‚ Emissions | ESG | Emission Intensity | COR-013 Carbon Footprint | −5 % emissions | > baseline target |
| **S2** | Increase Renewable Share | ESG | Renewable Share %, Energy Efficiency % | COR-014 Energy Transition | +10 % renewable | Renewable < 30 % |
| **S3** | Waste Recycling Initiative | ESG | Recycling Rate %, Sustainability Score | OPS-013 Circular Economy | +5 % recycling | Recycling rate < 60 % |
| **S4** | Supplier ESG Screening | ESG | Supplier ESG Compliance % | OPS-015 Supplier ESG | +5 % compliance | Supplier audit gaps > 10 % |
| **S5** | Supplier Decarbonization | ESG | Scope-3 Emissions %, ESG Score | COR-013 Supplier Carbon | −3 % scope-3 | Supplier emission > baseline |
| **S6** | Waste Reduction Program | ESG | Waste Rate %, Recycling Rate % | OPS-013 Waste Control | −10 % waste | Waste > target +10 % |
| **S7** | Sustainability Certification | ESG | ESG Score | COR-012 ESG Overview | +5 % ESG score | Certification missing |

---

### **Governance & Compliance**
| Code | Action | Impact Dimension | Target KPI | Typical Use Cases | Expected Effect | Trigger Condition |
|------|---------|------------------|-------------|-------------------|-----------------|-------------------|
| **GOV1** | Conduct Internal Audit | Governance | Compliance Breach Count | COR-016 Compliance Monitoring | 0 breaches | >1 major issue |
| **GOV2** | Data Quality Campaign | Governance | Data Quality Score % | COR-017 Data Quality Dashboard | +1 % quality | < 99 % integrity |
| **GOV3** | Security Patch Enforcement | Governance | Cyber Incident Count | COR-019 Security Monitoring | 0 critical | Incident detected |
| **GOV4** | Policy Update & Training | Governance | Policy Adherence % | COR-017 Policy Monitoring | +5 % adherence | < 90 % adherence |
| **GOV5** | BCP Update | Governance | Risk Index % | COR-018 Risk Management | −10 % risk | outdated > 1Y |
| **GOV6** | Access Review | Governance | Security Compliance %, OLS Coverage % | COR-019 Data Governance | 100 % compliance | Missing user audit |
| **GOV7** | Risk Heatmap Update | Governance | Risk Index | COR-018 Risk Monitoring | Updated quarterly | >3 months outdated |

---

### **Innovation & People**
| Code | Action | Impact Dimension | Target KPI | Typical Use Cases | Expected Effect | Trigger Condition |
|------|---------|------------------|-------------|-------------------|-----------------|-------------------|
| **I1** | Launch Innovation Sprint | Innovation & People | Innovation Index | COM-007 Innovation Effectiveness | +5 % index | Pipeline stagnation ≥ 3M |
| **I2** | Increase Training Hours | Innovation & People | Training Hours per FTE | COR-011 People Development | +5–10 % | < 10 h/FTE |
| **I3** | Improve Engagement | Innovation & People | Engagement Score | COR-010 HR Analytics | +3–5 pts | < 70 % engagement |
| **I4** | Promote Internal Mobility | Innovation & People | Internal Mobility Rate % | COR-010 HR Analytics | +2 % | < 5 % mobility |
| **I5** | Digitize Workflow | Innovation & People | Digital Adoption Rate % | COR-019 Digital Transformation | +10 % | Manual process ratio > 40 % |
| **I6** | Innovation Funnel Review | Innovation & People | Innovation ROI % | COM-008 Innovation ROI | +10 % | Pipeline stagnation |
| **I7** | Upskilling Program | Innovation & People | Training Hours per FTE | COR-011 Skill Development | +10 % | Training gap detected |
| **I8** | AI Pilot Launch | Innovation & People | Digital Adoption Rate %, Innovation Index | COR-019 AI Lab | +5–10 % efficiency | No AI projects > 6M |
| **I9** | Employer Branding Initiative | Innovation & People | Engagement Score, Turnover % | COR-010 HR Analytics | −1 pp turnover | Low applicant ratio |

---

## 4. Governance Rules
- Action Codes are **centrally maintained** under `_includes/ActionCodes.md`.  
- Each Use Case may reference multiple Action Codes, but each Action Code has one **primary KPI link**.  
- New codes must be proposed via Pull Request and approved by the **Governance Board**.  
- Codes are version-controlled and mirrored in Power BI metadata for Copilot readiness.

---

## 5. Cross-References
| File | Purpose |
|------|----------|
| [`/_includes/Strategic_KPIs.md`](./Strategic_KPIs.md) | Defines KPIs linked to each Action Code. |
| [`/_includes/kpi_catalog/README.md`](./kpi_catalog/README.md) | Contains full KPI definitions referenced by codes. |
| [`/docs/Methodology.md`](../docs/Methodology.md) | Explains linkage between KPIs, Actions, and visuals. |
| [`/docs/Reporting_Strategy.md`](../docs/Reporting_Strategy.md) | Provides governance layers and review workflow. |

---

_Last updated: 12.10.2025_




