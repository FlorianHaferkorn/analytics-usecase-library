---
id: "OPS-001"
title: "Cash Conversion Cycle (DSO + DIO − DPO)"
domain: "Operational Efficiency"
owner: "Head of Finance / Treasury"
impact: "High"
status: "Draft"
last_update: "07.10.2025"
---

# Cash Conversion Cycle (DSO + DIO − DPO)

## 1. Business Goal
Optimize working capital and liquidity by managing receivables, inventory, and payables efficiency — measured through the Cash Conversion Cycle (CCC).

---

## 2. Business Context
The CCC shows how long cash is tied up in operations before it returns through sales collections.  
Shortening this cycle releases cash and reduces financing needs.  
This use case unifies financial and operational perspectives to align Sales, Supply Chain, and Procurement on one liquidity KPI.

---

## 3. Key Questions
- How long does it take to convert operational investments into cash?  
- Which levers drive changes in DSO, DIO, and DPO?  
- Which customers or suppliers cause high working capital requirements?  
- How does inventory policy affect liquidity?  
- What scenarios can shorten the CCC without harming service levels?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| DSO (Days Sales Outstanding) | (Accounts Receivable ÷ Net Sales) × Days in Period | Days | 0 decimals |
| DIO (Days Inventory Outstanding) | (Inventory ÷ COGS) × Days in Period | Days | 0 decimals |
| DPO (Days Payables Outstanding) | (Accounts Payable ÷ COGS) × Days in Period | Days | 0 decimals |
| CCC (Cash Conversion Cycle) | DSO + DIO − DPO | Days | 0 decimals |
| Δ CCC | Current CCC − Plan or LY | Days | 0 decimals |

---

## 5. Required Attributes (Business-Level)
- Date (month end)  
- Org (legal entity, region)  
- AR Balance, AP Balance, Inventory Value  
- Net Sales Amount, COGS Amount  
- Days in Period (calendar mapping)  
- Optional: Supplier/Customer, Payment Terms, Country, Currency

---

## 6. Segmentation & Hierarchies
- Org: Company > Region > Country  
- Customer: Segment > Customer Group > Customer  
- Supplier: Group > Vendor  
- Product: Category > SKU  
- Time: Year > Month  

---

## 7. Scope & Assumptions
- Balances are period-end values.  
- Net Sales and COGS from monthly financials (P&L).  
- AR/AP balances reconciled with GL accounts.  
- Inventory from end-of-month stock snapshot.  
- Currency = EUR; FX translation at closing rate.  

---

## 8. Data Freshness & Cadence
- Refresh frequency: monthly (3rd business day after closing).  
- Latency ≤ 72h post-close.  
- Historical depth = 24 months.  
- Data Owner: Finance / Working Capital Team.  

---

## 9. Edge Cases & QA Rules
- AR/AP balances cannot be negative.  
- DSO capped at [0; 180] days, DIO at [0; 365].  
- Referential integrity ≥ 99.9 % across Date/Org.  
- Manual adjustments documented in audit log.  
- Currency differences reconciled within ±0.5 %.  

---

## 10. Minimum Viable Dataset (MVD)
- Required: Date, Org, AR, AP, Inventory, Net Sales, COGS.  
- Optional: Customer/Supplier, Payment Terms.  
- Extended: Country, Currency, FX Rate, Plan Data.  

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Accelerate collections via credit control and factoring | W1 | DSO −5–10 days |
| Optimize inventory levels and safety stocks | I1 | DIO −3–7 days |
| Negotiate extended supplier terms | W2 | DPO +5–10 days |
| Improve payment discipline and dunning automation | O2 | DSO −2 days; CCC −2 days |
| Align S&OP and Treasury on working capital targets | SP1 | CCC −5–8 days overall |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| Liquidity | +10–20 % free cash release | Δ CCC |
| Cost of Capital | −0.2–0.5 pp | vs prior FY |
| Service Level | ≥ 95 % OTIF (no degradation) | vs baseline |

---

## 13. Related Processes
Order-to-Cash · Purchase-to-Pay · Inventory Management · Treasury Forecasting · Financial Close.

---

## 14. Insights & Learnings
Companies often focus on DSO and DIO but overlook supplier payment discipline (DPO).  
Integrated CCC management reveals cross-functional trade-offs (e.g., inventory reduction vs supplier strain).

---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-002 Inventory Health](../02_Operational_Efficiency/OPS-002_Inventory_Health.md)`  
  `[OPS-003 Purchase Price Variance](../02_Operational_Efficiency/OPS-003_Purchase_Price_Variance.md)`  
  `[COM-002 Gross Margin Analysis](../01_Commercial/COM-002_Gross_Margin_Analysis.md)`  
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
