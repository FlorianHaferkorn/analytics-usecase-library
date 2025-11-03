---
id: "OPS-002"
title: "Inventory Health & Stock-Out Prevention"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Logistics"
impact: "High"
status: "Draft"
last_update: "07.10.2025"
supports_strategic_kpi: ["Working Capital %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "I2", "O2", "D1", "PC4"]
expected_impact: "-10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence"
---

# Inventory Health & Stock-Out Prevention

## 1. Business Goal
Ensure optimal stock levels by minimizing both overstock (capital tied up) and stock-outs (lost sales), balancing service levels and working capital efficiency.

---

## 2. Business Context
Inventory drives both liquidity and customer satisfaction.  
Excess stock blocks cash and increases markdown risk, while stock-outs harm revenue and brand perception.  
This use case enables proactive monitoring of inventory coverage, demand volatility, and replenishment performance to maintain the right balance at every node of the supply chain.

---

## 3. Key Questions
- Which SKUs or locations show excess or obsolete inventory?  
- Where do stock-outs or low coverage threaten sales?  
- What is the optimal target coverage given demand variability?  
- How does forecast accuracy affect safety stock?  
- What actions improve inventory turns without service loss?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Inventory Days | (Average Inventory / Daily COGS) | Days | 0 decimals |
| Stock-Out Rate % | Unfulfilled Demand / Total Demand | % | 1 decimal |
| Inventory Turnover | COGS / Average Inventory | Ratio | 2 decimals |
| Obsolescence % | Aged or blocked stock / Total Inventory | % | 1 decimal |
| OTIF % | On-Time In-Full deliveries / Total Deliveries | % | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Date (snapshot or daily balance)  
- Org (warehouse, store, region)  
- Product (category, subcategory, SKU)  
- Inventory Value, Units Qty  
- COGS Amount, Demand Qty, Delivered Qty  
- Optional: Safety Stock Target, Lead Time, Service Level Target

---

## 6. Segmentation & Hierarchies
- Org: Country > Region > Warehouse > Store  
- Product: Category > Subcategory > SKU  
- Time: Year > Month > Day  
- Segment: ABC/XYZ classification (value/volatility)

---

## 7. Scope & Assumptions
- Inventory valued at standard cost.  
- Daily snapshots aggregated to month-end for trend analysis.  
- Service Level = Delivered / Requested Qty.  
- Exclude consignment or third-party-managed stock.  
- Currency = EUR; reporting by company code.

---

## 8. Data Freshness & Cadence
- Refresh: daily (06:00 CET).  
- Latency <= 24 h.  
- Backfill = 12 months.  
- Data Owner: Supply Chain Analytics.

---

## 9. Edge Cases & QA Rules
- Inventory Value >= 0; Units Qty >= 0.  
- Stock-Out Rate % <= 100 %.  
- Referential integrity >= 99.9 % across Date/Org/Product.  
- Exclude discontinued items from active coverage ratio.  
- Safety Stock recalculated monthly based on updated demand volatility.

---

## 10. Minimum Viable Dataset (MVD)
- Required: Date, Org, Product, Inventory Value, Units Qty, COGS Amount, Demand Qty.  
- Optional: Delivered Qty, Safety Stock Target, Lead Time.  
- Extended: Product Lifecycle Phase, Reorder Point, Obsolescence Flag.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Adjust replenishment parameters (min/max levels, reorder points) | I1 | DIO -5-10 days; Stock-Outs reduce |
| Prioritize allocation of limited stock to high-margin SKUs or key stores | I2 | Revenue loss reduces; service stability improves |
| Reduce obsolete inventory via targeted markdown or redistribution | O2 | Inventory value reduces 5-10 % |
| Improve forecast accuracy through demand segmentation | D1 | Service improves; DIO stable |
| Strengthen supplier reliability (lead time, fill rate) | PC4 | OTIF improves; Stock-Outs reduce |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| Working Capital | -10-15 % Inventory Value | vs LY |
| Service Level | >= 97 % OTIF | vs baseline |
| Obsolescence | -20 % blocked stock | vs prior FY |

---

## 13. Related Processes
Replenishment Planning · Demand Forecasting · Procurement · S&OP · Warehouse Management.

---

## 14. Insights & Learnings
Inventory imbalances usually result more from planning latency than from forecast error.  
Linking forecast accuracy, replenishment discipline, and supplier reliability delivers the fastest ROI in working capital optimization.

---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-001 Cash Conversion Cycle](../02_Operational_Efficiency/OPS-001_Cash_Conversion_Cycle.md)`  
  `[OPS-003 Purchase Price Variance](../02_Operational_Efficiency/OPS-003_Purchase_Price_Variance.md)`  
  `[COM-002 Gross Margin Analysis](../01_Commercial/COM-002_Gross_Margin_Analysis.md)`  
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
