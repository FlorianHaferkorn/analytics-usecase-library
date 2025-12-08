---
id: "OPS-004"
title: "Replenishment Optimization & Service Level Management"
domain: "Operational Efficiency"
owner: "Head of Supply Chain Planning"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Operational"
analytics_stage: "Prescriptive"
supports_strategic_kpi: ["Service Level %", "Stock-Out Rate %", "Inventory Days"]
supports_strategic_kpi_ids: ["ops.otif.pct", "ops.stockout.pct", "ops.inventory.days"]
action_codes: ["I1", "PC4", "I2", "O2", "SP1"]
expected_impact: "+2-3 pp Service Level; -5-10 % Inventory Value; -20 % forecast MAPE"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Supplier.Group>Vendor",
  "Time.Year>Month>Week"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "ServiceLevel_Bounds", "LeadTime_Positive"]
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
data_requirements:
  facts:
    - name: fact_replenishment_order
      grain: order_line
      primary_key: [OrderID, OrderLine]
      required_columns:
        - { name: OrderDate, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: SupplierID, type: string, role: supplier_key }
        - { name: "Order Qty", type: decimal, role: quantity }
        - { name: "Forecast Qty", type: decimal, role: quantity }
        - { name: "Safety Stock Qty", type: decimal, role: helper }
        - { name: "Reorder Point Qty", type: decimal, role: helper }
        - { name: "Lead Time Days", type: int, role: helper }
    - name: fact_fulfillment
      grain: delivery_line
      primary_key: [DeliveryID, DeliveryLine]
      required_columns:
        - { name: DeliveryDate, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Delivered Qty", type: decimal, role: quantity }
        - { name: "Demand Qty", type: decimal, role: quantity }
        - { name: "Stock-Out Flag", type: bool, role: indicator }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_product
      grain: product
      primary_key: [ProductID]
    - name: dim_supplier
      grain: supplier
      primary_key: [SupplierID]
  relationships:
    - { from: fact_replenishment_order.OrderDate, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_replenishment_order.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_replenishment_order.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_fulfillment.DeliveryDate, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_fulfillment.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_fulfillment.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_replenishment_order.SupplierID, to: dim_supplier.SupplierID, cardinality: many-to-one, direction: single }
model_mapping:
  "Order Qty": "fact_replenishment_order[Order Qty]"
  "Delivered Qty": "fact_fulfillment[Delivered Qty]"
  "Demand Qty": "fact_fulfillment[Demand Qty]"
  "Forecast Qty": "fact_replenishment_order[Forecast Qty]"
  "Safety Stock Qty": "fact_replenishment_order[Safety Stock Qty]"
  "Reorder Point Qty": "fact_replenishment_order[Reorder Point Qty]"
  "Lead Time Days": "fact_replenishment_order[Lead Time Days]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
  "Supplier": "dim_supplier[SupplierID]"
---

# Replenishment Optimization & Service Level Management - Business Factsheet

## 1. Summary
- **Business Goal:** Optimize replenishment parameters and order logic to balance service levels, minimize inventory costs, and reduce lost sales due to stock-outs or delayed replenishment.
- **Target Audience:** Head of Supply Chain Planning
- **Business Priority:** High
- **Expected Impact:** +2-3 pp Service Level; -5-10 % Inventory Value; -20 % forecast MAPE

## 2. Core Questions
- Are replenishment quantities aligned with real demand and forecast accuracy?
- Which items or stores frequently under- or over-order?
- How does supplier lead time variability affect service levels?
- Where can replenishment frequency or batch sizes be optimized?
- Which actions yield the best trade-off between cost and service?

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Replenishment Adherence % | Orders placed / Orders suggested by system | % | 1 decimal |
| Order Accuracy % | Delivered Qty / Ordered Qty | % | 1 decimal |
| Stock-Out Rate % | Demand not fulfilled / Total demand | % | 1 decimal |
| Inventory Days | Inventory / COGS x 365 | days | 0 decimals |
| OTIF % | On-time, in-full deliveries / Total orders | % | 1 decimal |

## 4. Business Logic & Thresholds
- Reorder Point >= 0; Safety Stock >= 0.
- Negative order quantities excluded.
- Service Level % capped at [0; 100].
- Lead Time deviations > 3 standard deviations flagged.
- Referential integrity >= 99.9 % across Date/Org/Product/Supplier.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Adjust reorder points based on forecast error and demand variability | I1 | Stock-Outs reduce; Inventory -5-10 % |
| Synchronize supplier delivery cadence with actual consumption patterns | PC4 | Lead Time reduces; OTIF improves |
| Implement dynamic safety stock based on target service level | I2 | Service improves; working capital stable |
| Reduce order batch sizes to avoid overstock | O2 | Inventory Days -5; obsolescence reduces |
| Integrate replenishment optimization into S&OP | SP1 | Forecast accuracy improves; liquidity improves |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Replenishment Adherence %, Order Accuracy %, Stock-Out Rate %, Inventory Days, OTIF % with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Customer drill-down.
- Drill-through to transactional detail (orders/invoices).
- Export-ready table including action status.

## 7. Dependencies & Constraints
- Replenishment logic based on EOQ or Min/Max policy per SKU.
- Demand forecast updated weekly (rolling horizon).
- Lead times from supplier master, adjusted by historical average.
- Service Level Target defined by category (A: 98 %, B: 95 %, C: 90 %).
- Currency = EUR; values aggregated by store and category.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Service Level | +2-3 pp OTIF | vs Plan |
| Working Capital | Inventory value -5-10 % | vs Prior Quarter |
| Forecast Quality | MAPE -20 % | 13-week horizon |