---
id: "OPS-003"
title: "Purchase Price Variance (PPV) & Supplier Performance"
domain: "Operational Efficiency"
owner: "Head of Procurement Controlling"
impact: "High"
status: "Draft"
last_update: "07.10.2025"
supports_strategic_kpi: ["COGS % of Sales", "Gross Margin %", "Supplier OTIF %"]
action_codes: ["PC2", "O2", "PC4", "SP1", "PC3"]
expected_impact: "-2-4 % average COGS; +5-10 pp OTIF; +10-20 % verified savings"
---

# Purchase Price Variance (PPV) & Supplier Performance

## 1. Business Goal
Control and reduce material costs by identifying deviations between actual and contracted purchase prices, evaluating supplier performance, and enabling proactive negotiation and sourcing actions.

---

## 2. Business Context
Procurement price discipline directly impacts gross margin and cost of goods sold (COGS).  
Actual purchase prices often deviate from contract conditions due to indexation, rebates, or timing effects.  
This use case provides transparency on cost variance, supplier reliability, and sourcing efficiency, linking operational data with financial impact.

---

## 3. Key Questions
- What is the Δ and Δ% between actual and contracted purchase prices?  
- Which suppliers or materials contribute most to PPV?  
- Are deviations caused by market prices, indexation, or process inefficiencies?  
- How reliable are suppliers in pricing and delivery (OTIF, cost adherence)?  
- Where should procurement focus renegotiation or rebid efforts?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| PPV % | (Actual Price - Contract Price) / Contract Price | % | 1 decimal |
| PPV Amount | (Actual Price - Contract Price) × Quantity | EUR | 0-2 decimals |
| Contract Compliance % | Purchases at agreed price / Total purchases | % | 1 decimal |
| Supplier OTIF % | On-Time In-Full deliveries / Total deliveries | % | 1 decimal |
| Δ COGS Amount | Change in total procurement cost vs Plan | EUR | 0-2 decimals |

---

## 5. Required Attributes (Business-Level)
- Date (purchase order or GR date)  
- Org (plant, region, company)  
- Supplier ID, Supplier Name  
- Material ID, Material Group, Category  
- Actual Unit Price, Contract Unit Price, Quantity, COGS Amount  
- Optional: Indexation Type, Currency, Purchase Order ID, Delivery Date

---

## 6. Segmentation & Hierarchies
- Supplier: Group > Vendor > Material  
- Material: Category > Subcategory > SKU  
- Org: Company > Region > Plant  
- Time: Year > Month > Week  

---

## 7. Scope & Assumptions
- PPV = (Actual Price - Contract Price) / Contract Price.  
- Contract Price derived from latest valid agreement (effective date <= order date).  
- Exclude freight or overhead costs unless specified in agreement.  
- Currency = EUR; FX translation at posting date.  
- Negative PPV (price gain) treated as positive variance for savings tracking.

---

## 8. Data Freshness & Cadence
- Refresh frequency: weekly (Monday 07:00 CET).  
- Latency <= 3 days after PO goods receipt.  
- Historical depth = 24 months.  
- Data Owner: Procurement Analytics / Controlling.

---

## 9. Edge Cases & QA Rules
- Actual and Contract Price must be > 0.  
- PPV % capped between [-50%; +100%].  
- Missing contract references flagged as 'No Valid Contract'.  
- Supplier master must reconcile with vendor list.  
- Referential integrity >= 99.9 % across Date/Org/Supplier/Material.

---

## 10. Minimum Viable Dataset (MVD)
- Required: Date, Supplier, Material, Actual Price, Contract Price, Quantity.  
- Optional: COGS Amount, Currency, Delivery Date.  
- Extended: Indexation Type, Payment Terms, Lead Time, OTIF Metrics.

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

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| Cost Reduction | -2-4 % average COGS | vs LY |
| Supplier Reliability | +5-10 pp OTIF | vs baseline |
| Savings Realization | +10-20 % verified savings vs plan | year-to-date |

---

## 13. Related Processes
Source-to-Contract · Procure-to-Pay · Supplier Management · Financial Planning & Analysis.

---

## 14. Insights & Learnings
PPV transparency often reveals hidden process issues such as delayed contract updates or duplicate suppliers.  
Supplier consolidation and proactive rebid cycles generate higher savings than short-term price pressure.

---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-001 Cash Conversion Cycle](../02_Operational_Efficiency/OPS-001_Cash_Conversion_Cycle.md)`  
  `[COM-002 Gross Margin Analysis](../01_Commercial/COM-002_Gross_Margin_Analysis.md)`  
  `[COR-001 Project ROI Tracking](../04_Corporate_and_Strategy/COR-001_Project_ROI_and_Benefit_Tracking.md)`  
- Related Documents:  
  [`KPI Catalog`](../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../_includes/ActionCodes.md) | [`Glossary`](../../_includes/Glossary.md)

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
