---
id: "OPS-002"
title: "Inventory Health & Stock-Out Prevention"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Logistics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Working Capital %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "I2", "O2", "D1", "PC4"]
expected_impact: "-10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence"
required_kpi_ids: [
  "ops.inventory.days",
  "ops.stockout.pct",
  "ops.inventory.turnover",
  "ops.inventory.obsolescence.pct",
  "ops.otif.pct"
]
required_kpis:
  ops.inventory.days: "Inventory Days"
  ops.stockout.pct: "Stock-Out Rate %"
  ops.inventory.turnover: "Inventory Turnover"
  ops.inventory.obsolescence.pct: "Obsolescence %"
  ops.otif.pct: "OTIF %"
---

# Inventory Health & Stock-Out Prevention

## 1. Business Goal
Ensure optimal stock levels by minimizing both overstock (capital tied up) and stock-outs (lost sales), balancing service levels and working capital efficiency.

---
id: "OPS-002"
title: "Inventory Health & Stock-Out Prevention"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Logistics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Working Capital %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "I2", "O2", "D1", "PC4"]
expected_impact: "-10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence"
required_kpi_ids: []
required_kpis: {}
---

## 3. Key Questions
- Which SKUs or locations show excess or obsolete inventory?  
- Where do stock-outs or low coverage threaten sales?  
- What is the optimal target coverage given demand variability?  
- How does forecast accuracy affect safety stock?  
- What actions improve inventory turns without service loss?

---
id: "OPS-002"
title: "Inventory Health & Stock-Out Prevention"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Logistics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Working Capital %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "I2", "O2", "D1", "PC4"]
expected_impact: "-10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence"
required_kpi_ids: []
required_kpis: {}
---

## 5. Required Attributes (Business-Level)
- Date (snapshot or daily balance)  
- Org (warehouse, store, region)  
- Product (category, subcategory, SKU)  
- Inventory Value, Units Qty  
- COGS Amount, Demand Qty, Delivered Qty  
- Optional: Safety Stock Target, Lead Time, Service Level Target

---
id: "OPS-002"
title: "Inventory Health & Stock-Out Prevention"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Logistics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Working Capital %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "I2", "O2", "D1", "PC4"]
expected_impact: "-10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence"
required_kpi_ids: []
required_kpis: {}
---

## 7. Scope & Assumptions
- Inventory valued at standard cost.  
- Daily snapshots aggregated to month-end for trend analysis.  
- Service Level = Delivered / Requested Qty.  
- Exclude consignment or third-party-managed stock.  
- Currency = EUR; reporting by company code.

---
id: "OPS-002"
title: "Inventory Health & Stock-Out Prevention"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Logistics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Working Capital %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "I2", "O2", "D1", "PC4"]
expected_impact: "-10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence"
required_kpi_ids: []
required_kpis: {}
---

## 9. Edge Cases & QA Rules
- Inventory Value >= 0; Units Qty >= 0.  
- Stock-Out Rate % <= 100 %.  
- Referential integrity >= 99.9 % across Date/Org/Product.  
- Exclude discontinued items from active coverage ratio.  
- Safety Stock recalculated monthly based on updated demand volatility.

---
id: "OPS-002"
title: "Inventory Health & Stock-Out Prevention"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Logistics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Working Capital %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "I2", "O2", "D1", "PC4"]
expected_impact: "-10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence"
required_kpi_ids: []
required_kpis: {}
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
id: "OPS-002"
title: "Inventory Health & Stock-Out Prevention"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Logistics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Working Capital %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "I2", "O2", "D1", "PC4"]
expected_impact: "-10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence"
required_kpi_ids: []
required_kpis: {}
---

## 13. Related Processes
Replenishment Planning -> Demand Forecasting -> Procurement -> S&OP -> Warehouse Management.

---
id: "OPS-002"
title: "Inventory Health & Stock-Out Prevention"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Logistics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Working Capital %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "I2", "O2", "D1", "PC4"]
expected_impact: "-10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence"
required_kpi_ids: []
required_kpis: {}
---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-001 Cash Conversion Cycle](../OPS-001_Cash_Conversion_Cycle/FactSheet.md)`  
  `[OPS-003 Purchase Price Variance](../OPS-003_Purchase_Price_Variance/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

---
id: "OPS-002"
title: "Inventory Health & Stock-Out Prevention"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Logistics"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Working Capital %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "I2", "O2", "D1", "PC4"]
expected_impact: "-10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence"
required_kpi_ids: []
required_kpis: {}
---

_Last updated: 03.11.2025_

