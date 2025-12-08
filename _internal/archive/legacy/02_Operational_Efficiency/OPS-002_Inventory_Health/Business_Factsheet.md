---
id: "OPS-002"
title: "Inventory Health & Stock-Out Prevention"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Logistics"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Operational"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Working Capital %", "Stock-Out Rate %", "Inventory Days"]
supports_strategic_kpi_ids: ["ops.working_capital.pct", "ops.stockout.pct", "ops.inventory.days"]
action_codes: ["I1", "I2", "O2", "D1", "PC4"]
expected_impact: "-10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Channel",
  "Time.Year>Month>Week"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "Inventory_Value_Positive", "Coverage_InRange"]
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
data_requirements:
  facts:
    - name: fact_inventory_snapshot
      grain: sku_location_day
      primary_key: [SnapshotDate, OrgID, ProductID]
      required_columns:
        - { name: SnapshotDate, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Inventory Units", type: decimal, role: quantity }
        - { name: "Inventory Value", type: decimal, role: amount }
        - { name: "Demand Qty", type: decimal, role: quantity }
        - { name: "Delivered Qty", type: decimal, role: quantity }
        - { name: "Safety Stock Qty", type: decimal, role: helper }
        - { name: "Lead Time Days", type: int, role: helper }
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "COGS Amount", type: decimal, role: amount }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Warehouse, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
  relationships:
    - { from: fact_inventory_snapshot.SnapshotDate, to: dim_date.Date, cardinality: many-to-one, direction: single, ri_expected: ">=99.5%" }
    - { from: fact_inventory_snapshot.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_inventory_snapshot.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
model_mapping:
  "Inventory Units": "fact_inventory_snapshot[Inventory Units]"
  "Inventory Value": "fact_inventory_snapshot[Inventory Value]"
  "Demand Qty": "fact_inventory_snapshot[Demand Qty]"
  "Delivered Qty": "fact_inventory_snapshot[Delivered Qty]"
  "Safety Stock Qty": "fact_inventory_snapshot[Safety Stock Qty]"
  "Lead Time Days": "fact_inventory_snapshot[Lead Time Days]"
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "COGS Amount": "fact_sales[COGS Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Inventory Health & Stock-Out Prevention - Business Factsheet

## 1. Summary
- **Business Goal:** Ensure optimal stock levels by minimizing both overstock (capital tied up) and stock-outs (lost sales), balancing service levels and working capital efficiency.
- **Target Audience:** Head of Supply Chain / Logistics
- **Business Priority:** High
- **Expected Impact:** -10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence

## 2. Core Questions
- Which SKUs or locations show excess or obsolete inventory?
- Where do stock-outs or low coverage threaten sales?
- What is the optimal target coverage given demand variability?
- How does forecast accuracy affect safety stock?
- What actions improve inventory turns without service loss?

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Inventory Days | Inventory Value / COGS * 365 | days | 0 decimals |
| Stock-Out Rate % | Lost demand / Requested demand | % | 1 decimal |
| Inventory Turnover | COGS / Average Inventory | x | 1 decimal |
| Obsolescence % | (Aged Stock > Threshold) / Total Inventory | % | 1 decimal |
| OTIF % | On-Time In-Full Deliveries / Orders | % | 1 decimal |

## 4. Business Logic & Thresholds
- Inventory Value >= 0; Units Qty >= 0.
- Stock-Out Rate % <= 100 %.
- Referential integrity >= 99.9 % across Date/Org/Product.
- Exclude discontinued items from active coverage ratio.
- Safety Stock recalculated monthly based on updated demand volatility.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Adjust replenishment parameters (min/max levels, reorder points) | I1 | DIO -5-10 days; Stock-Outs reduce |
| Prioritize allocation of limited stock to high-margin SKUs or key stores | I2 | Revenue loss reduces; service stability improves |
| Reduce obsolete inventory via targeted markdown or redistribution | O2 | Inventory value reduces 5-10 % |
| Improve forecast accuracy through demand segmentation | D1 | Service improves; DIO stable |
| Strengthen supplier reliability (lead time, fill rate) | PC4 | OTIF improves; Stock-Outs reduce |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Inventory Days, Stock-Out Rate %, Inventory Turnover, Obsolescence %, OTIF % with Plan/LY deltas.
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
- Inventory valued at standard cost; adjustments logged separately.
- Daily snapshots aggregated to month-end for trend analysis.
- Service Level = Delivered / Requested Qty; OTIF pulled from fulfillment system.
- Exclude consignment or third-party-managed stock.
- Currency = EUR; reporting by company code.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Working Capital | Inventory value -10-15 % | vs Plan |
| Service Level | OTIF >= 97 %; Stock-Out Rate <= 3 % | weekly dashboard |
| Obsolescence | Slow-mover share -20 % | vs Prior Quarter |