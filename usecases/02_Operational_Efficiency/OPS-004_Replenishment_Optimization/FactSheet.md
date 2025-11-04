---
id: "OPS-004"
title: "Replenishment Optimization & Service Level Management"
domain: "Operational Efficiency"
owner: "Head of Supply Chain Planning"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Service Level %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "PC4", "I2", "O2", "SP1"]
expected_impact: "+2-3 pp Service Level; -5-10 % Inventory Value; -20 % forecast MAPE"
required_kpi_ids: [
  "ops.replenishment.adherence.pct",
  "ops.order_accuracy.pct",
  "ops.stockout.pct",
  "ops.inventory.days",
  "ops.otif.pct"
]
required_kpis:
  ops.replenishment.adherence.pct: "Replenishment Adherence %"
  ops.order_accuracy.pct: "Order Accuracy %"
  ops.stockout.pct: "Stock-Out Rate %"
  ops.inventory.days: "Inventory Days"
  ops.otif.pct: "OTIF %"
---

# Replenishment Optimization & Service Level Management

## 1. Business Goal
Optimize replenishment parameters and order logic to balance service levels, minimize inventory costs, and reduce lost sales due to stock-outs or delayed replenishment.

---
id: "OPS-004"
title: "Replenishment Optimization & Service Level Management"
domain: "Operational Efficiency"
owner: "Head of Supply Chain Planning"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Service Level %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "PC4", "I2", "O2", "SP1"]
expected_impact: "+2-3 pp Service Level; -5-10 % Inventory Value; -20 % forecast MAPE"
required_kpi_ids: []
required_kpis: {}
---

## 3. Key Questions
- Are replenishment quantities aligned with real demand and forecast accuracy?  
- Which items or stores frequently under- or over-order?  
- How does supplier lead time variability affect service levels?  
- Where can replenishment frequency or batch sizes be optimized?  
- Which actions yield the best trade-off between cost and service?

---
id: "OPS-004"
title: "Replenishment Optimization & Service Level Management"
domain: "Operational Efficiency"
owner: "Head of Supply Chain Planning"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Service Level %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "PC4", "I2", "O2", "SP1"]
expected_impact: "+2-3 pp Service Level; -5-10 % Inventory Value; -20 % forecast MAPE"
required_kpi_ids: []
required_kpis: {}
---

## 5. Required Attributes (Business-Level)
- Date (order date / delivery date)  
- Org (store, warehouse, region)  
- Product (category, subcategory, SKU)  
- Ordered Qty, Delivered Qty, Demand Qty  
- Lead Time (days), Target Stock, Safety Stock, Reorder Point  
- Optional: Supplier, Promo Flag, Forecast Qty  

---
id: "OPS-004"
title: "Replenishment Optimization & Service Level Management"
domain: "Operational Efficiency"
owner: "Head of Supply Chain Planning"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Service Level %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "PC4", "I2", "O2", "SP1"]
expected_impact: "+2-3 pp Service Level; -5-10 % Inventory Value; -20 % forecast MAPE"
required_kpi_ids: []
required_kpis: {}
---

## 7. Scope & Assumptions
- Replenishment logic based on EOQ or Min/Max policy per SKU.  
- Demand forecast updated weekly (rolling horizon).  
- Lead times from supplier master, adjusted by historical average.  
- Service Level Target defined by category (A: 98 %, B: 95 %, C: 90 %).  
- Currency = EUR; values aggregated by store and category.

---
id: "OPS-004"
title: "Replenishment Optimization & Service Level Management"
domain: "Operational Efficiency"
owner: "Head of Supply Chain Planning"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Service Level %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "PC4", "I2", "O2", "SP1"]
expected_impact: "+2-3 pp Service Level; -5-10 % Inventory Value; -20 % forecast MAPE"
required_kpi_ids: []
required_kpis: {}
---

## 9. Edge Cases & QA Rules
- Reorder Point >= 0; Safety Stock >= 0.  
- Negative order quantities excluded.  
- Service Level % capped at [0; 100].  
- Lead Time deviations > 3σ standard deviation flagged.  
- Referential integrity >= 99.9 % across Date/Org/Product/Supplier.

---
id: "OPS-004"
title: "Replenishment Optimization & Service Level Management"
domain: "Operational Efficiency"
owner: "Head of Supply Chain Planning"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Service Level %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "PC4", "I2", "O2", "SP1"]
expected_impact: "+2-3 pp Service Level; -5-10 % Inventory Value; -20 % forecast MAPE"
required_kpi_ids: []
required_kpis: {}
---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Adjust reorder points based on forecast error and demand variability | I1 | Stock-Outs reduce; Inventory -5-10 % |
| Synchronize supplier delivery cadence with actual consumption patterns | PC4 | Lead Time reduces; OTIF improves |
| Implement dynamic safety stock based on target service level | I2 | Service improves; working capital stable |
| Reduce order batch sizes to avoid overstock | O2 | Inventory Days -5; obsolescence reduces |
| Integrate replenishment optimization into S&OP | SP1 | Forecast accuracy improves; liquidity improves |

---
id: "OPS-004"
title: "Replenishment Optimization & Service Level Management"
domain: "Operational Efficiency"
owner: "Head of Supply Chain Planning"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Service Level %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "PC4", "I2", "O2", "SP1"]
expected_impact: "+2-3 pp Service Level; -5-10 % Inventory Value; -20 % forecast MAPE"
required_kpi_ids: []
required_kpis: {}
---

## 13. Related Processes
Replenishment Planning -> Inventory Optimization -> Supplier Collaboration -> Demand Forecasting -> S&OP.

---
id: "OPS-004"
title: "Replenishment Optimization & Service Level Management"
domain: "Operational Efficiency"
owner: "Head of Supply Chain Planning"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Service Level %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "PC4", "I2", "O2", "SP1"]
expected_impact: "+2-3 pp Service Level; -5-10 % Inventory Value; -20 % forecast MAPE"
required_kpi_ids: []
required_kpis: {}
---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-002 Inventory Health](../OPS-002_Inventory_Health/FactSheet.md)`  
  `[OPS-003 Purchase Price Variance](../OPS-003_Purchase_Price_Variance/FactSheet.md)`  
  `[COM-001 Sales Performance](../../01_Commercial/COM-001_Sales_Performance/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

---
id: "OPS-004"
title: "Replenishment Optimization & Service Level Management"
domain: "Operational Efficiency"
owner: "Head of Supply Chain Planning"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Service Level %", "Stock-Out Rate %", "Inventory Days"]
action_codes: ["I1", "PC4", "I2", "O2", "SP1"]
expected_impact: "+2-3 pp Service Level; -5-10 % Inventory Value; -20 % forecast MAPE"
required_kpi_ids: []
required_kpis: {}
---

_Last updated: 03.11.2025_

