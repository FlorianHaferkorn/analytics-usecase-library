---
id: "OPS-003"
title: "Purchase Price Variance (PPV) & Supplier Performance"
domain: "Operational Efficiency"
owner: "Head of Procurement Controlling"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["COGS % of Sales", "Gross Margin %", "Supplier OTIF %"]
action_codes: ["PC2", "O2", "PC4", "SP1", "PC3"]
expected_impact: "-2-4 % average COGS; +5-10 pp OTIF; +10-20 % verified savings"
required_kpi_ids: [
  "ops.ppv.pct",
  "ops.ppv.amount",
  "ops.contract.compliance.pct",
  "ops.otif.pct"
]
required_kpis:
  ops.ppv.pct: "PPV %"
  ops.ppv.amount: "PPV Amount"
  ops.contract.compliance.pct: "Contract Compliance %"
  ops.otif.pct: "OTIF %"
---

# Purchase Price Variance (PPV) & Supplier Performance

## 1. Business Goal
Control and reduce material costs by identifying deviations between actual and contracted purchase prices, evaluating supplier performance, and enabling proactive negotiation and sourcing actions.

---
id: "OPS-003"
title: "Purchase Price Variance (PPV) & Supplier Performance"
domain: "Operational Efficiency"
owner: "Head of Procurement Controlling"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["COGS % of Sales", "Gross Margin %", "Supplier OTIF %"]
action_codes: ["PC2", "O2", "PC4", "SP1", "PC3"]
expected_impact: "-2-4 % average COGS; +5-10 pp OTIF; +10-20 % verified savings"
required_kpi_ids: []
required_kpis: {}
---

## 3. Key Questions
- What is the Δ and Δ% between actual and contracted purchase prices?  
- Which suppliers or materials contribute most to PPV?  
- Are deviations caused by market prices, indexation, or process inefficiencies?  
- How reliable are suppliers in pricing and delivery (OTIF, cost adherence)?  
- Where should procurement focus renegotiation or rebid efforts?

---
id: "OPS-003"
title: "Purchase Price Variance (PPV) & Supplier Performance"
domain: "Operational Efficiency"
owner: "Head of Procurement Controlling"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["COGS % of Sales", "Gross Margin %", "Supplier OTIF %"]
action_codes: ["PC2", "O2", "PC4", "SP1", "PC3"]
expected_impact: "-2-4 % average COGS; +5-10 pp OTIF; +10-20 % verified savings"
required_kpi_ids: []
required_kpis: {}
---

## 5. Required Attributes (Business-Level)
- Date (purchase order or GR date)  
- Org (plant, region, company)  
- Supplier ID, Supplier Name  
- Material ID, Material Group, Category  
- Actual Unit Price, Contract Unit Price, Quantity, COGS Amount  
- Optional: Indexation Type, Currency, Purchase Order ID, Delivery Date

---
id: "OPS-003"
title: "Purchase Price Variance (PPV) & Supplier Performance"
domain: "Operational Efficiency"
owner: "Head of Procurement Controlling"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["COGS % of Sales", "Gross Margin %", "Supplier OTIF %"]
action_codes: ["PC2", "O2", "PC4", "SP1", "PC3"]
expected_impact: "-2-4 % average COGS; +5-10 pp OTIF; +10-20 % verified savings"
required_kpi_ids: []
required_kpis: {}
---

## 7. Scope & Assumptions
- PPV = (Actual Price - Contract Price) / Contract Price.  
- Contract Price derived from latest valid agreement (effective date <= order date).  
- Exclude freight or overhead costs unless specified in agreement.  
- Currency = EUR; FX translation at posting date.  
- Negative PPV (price gain) treated as positive variance for savings tracking.

---
id: "OPS-003"
title: "Purchase Price Variance (PPV) & Supplier Performance"
domain: "Operational Efficiency"
owner: "Head of Procurement Controlling"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["COGS % of Sales", "Gross Margin %", "Supplier OTIF %"]
action_codes: ["PC2", "O2", "PC4", "SP1", "PC3"]
expected_impact: "-2-4 % average COGS; +5-10 pp OTIF; +10-20 % verified savings"
required_kpi_ids: []
required_kpis: {}
---

## 9. Edge Cases & QA Rules
- Actual and Contract Price must be > 0.  
- PPV % capped between [-50%; +100%].  
- Missing contract references flagged as 'No Valid Contract'.  
- Supplier master must reconcile with vendor list.  
- Referential integrity >= 99.9 % across Date/Org/Supplier/Material.

---
id: "OPS-003"
title: "Purchase Price Variance (PPV) & Supplier Performance"
domain: "Operational Efficiency"
owner: "Head of Procurement Controlling"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["COGS % of Sales", "Gross Margin %", "Supplier OTIF %"]
action_codes: ["PC2", "O2", "PC4", "SP1", "PC3"]
expected_impact: "-2-4 % average COGS; +5-10 pp OTIF; +10-20 % verified savings"
required_kpi_ids: []
required_kpis: {}
---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Renegotiate supplier terms and pricing | PC2 | COGS -1-3 %; GM % +0.5 pp |
| Enforce contract price adherence and prevent off-contract spend | O2 | Contract Compliance improves; PPV reduces |
| Implement supplier scorecards for cost, quality, delivery | PC4 | OTIF improves; PPV variability reduces |
| Consolidate spend to preferred suppliers | SP1 | Scale leverage improves; COGS reduces |
| Adjust procurement indexation policy | PC3 | PPV volatility reduces 30 % |

---
id: "OPS-003"
title: "Purchase Price Variance (PPV) & Supplier Performance"
domain: "Operational Efficiency"
owner: "Head of Procurement Controlling"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["COGS % of Sales", "Gross Margin %", "Supplier OTIF %"]
action_codes: ["PC2", "O2", "PC4", "SP1", "PC3"]
expected_impact: "-2-4 % average COGS; +5-10 pp OTIF; +10-20 % verified savings"
required_kpi_ids: []
required_kpis: {}
---

## 13. Related Processes
Source-to-Contract -> Procure-to-Pay -> Supplier Management -> Financial Planning & Analysis.

---
id: "OPS-003"
title: "Purchase Price Variance (PPV) & Supplier Performance"
domain: "Operational Efficiency"
owner: "Head of Procurement Controlling"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["COGS % of Sales", "Gross Margin %", "Supplier OTIF %"]
action_codes: ["PC2", "O2", "PC4", "SP1", "PC3"]
expected_impact: "-2-4 % average COGS; +5-10 pp OTIF; +10-20 % verified savings"
required_kpi_ids: []
required_kpis: {}
---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-001 Cash Conversion Cycle](../OPS-001_Cash_Conversion_Cycle/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
  `[COR-001 Project ROI Tracking](../../04_Corporate_and_Strategy/COR-001_Project_ROI_and_Benefit_Tracking/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

---
id: "OPS-003"
title: "Purchase Price Variance (PPV) & Supplier Performance"
domain: "Operational Efficiency"
owner: "Head of Procurement Controlling"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["COGS % of Sales", "Gross Margin %", "Supplier OTIF %"]
action_codes: ["PC2", "O2", "PC4", "SP1", "PC3"]
expected_impact: "-2-4 % average COGS; +5-10 pp OTIF; +10-20 % verified savings"
required_kpi_ids: []
required_kpis: {}
---

_Last updated: 03.11.2025_

