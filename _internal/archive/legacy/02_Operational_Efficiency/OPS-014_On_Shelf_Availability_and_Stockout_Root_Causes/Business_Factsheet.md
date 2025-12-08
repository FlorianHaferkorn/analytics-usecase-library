---
id: "OPS-014"
title: "On-Shelf Availability & Stockout Root Causes"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Retail Operations"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Service Level %", "Revenue Growth %"]
supports_strategic_kpi_ids:
  ["ops.otif.pct", "sales.revenue.growth_pct"]
action_codes: ["I1", "I2", "D1", "O2"]
expected_impact: "Improve on-shelf availability by identifying where along the supply chain stockouts are created and which actions prevent lost sales."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>Store",
    "Product.Category>Subcategory>SKU",
    "Time.Year>Month>Week",
  ]
filters_default: ["Time: Last 12W", "Org: All"]
qa_asserts: ["Stockout_Definition_Documented", "Service_Level_Consistent"]
required_kpi_ids:
  [
    "ops.stockout.pct",
    "ops.otif.pct",
    "ops.order_accuracy.pct",
    "sales.net_sales.amount",
  ]
required_kpis:
  ops.stockout.pct: "Stockout Rate %"
  ops.otif.pct: "On-Time-In-Full (OTIF) %"
  ops.order_accuracy.pct: "Order Accuracy %"
  sales.net_sales.amount: "Net Sales Amount"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
    - name: fact_service_level
      grain: org_product_period
      primary_key: [OrgID, ProductID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Order Lines Total", type: int, role: quantity }
        - { name: "Order Lines Stockout", type: int, role: quantity }
        - { name: "Order Lines OTIF", type: int, role: quantity }
        - { name: "Order Lines Accurate", type: int, role: quantity }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
        - { name: Week, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Store, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Order Lines Total": "fact_service_level[Order Lines Total]"
  "Order Lines Stockout": "fact_service_level[Order Lines Stockout]"
  "Order Lines OTIF": "fact_service_level[Order Lines OTIF]"
  "Order Lines Accurate": "fact_service_level[Order Lines Accurate]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# On-Shelf Availability & Stockout Root Causes - Business Factsheet

## 1. Summary
- **Business Goal:** Increase on-shelf availability and avoid lost sales by understanding where stockouts are generated along the supply chain and which root causes dominate.
- **Target Audience:** Head of Supply Chain / Retail Operations
- **Business Priority:** High
- **Expected Impact:** Improve on-shelf availability by identifying where along the supply chain stockouts are created and which actions prevent lost sales.

## 2. Core Questions
- Wo (Region, Store, Kategorie) treten die meisten Stockouts auf und wie gro ist der resultierende Umsatzverlust?
- Welche Root Causes dominieren: Forecast-Fehler, falsche Bestellmengen, Kommissionierfehler, Transportverzgerungen oder In-Store-Handling?
- Welche Kombination aus Manahmen (Parameteranpassungen, Prozessnderungen, Training) liefert den grten Service-Level-Gewinn?

## 3. KPI Set (Business View)
| KPI | Definition | Unit |
|-----|------------|------|
| Stockout Rate % | Stockout Order Lines / Total Order Lines | % |
| OTIF % | On-Time-In-Full deliveries / Total deliveries | % |
| Order Accuracy % | Correctly picked/shipped order lines / Total order lines | % |
| Net Sales Amount | Sales revenue, used to quantify lost sales | EUR |

## 4. Business Logic & Thresholds
- Returns, Stornos und Nachlieferungen mssen je nach Definition in Order-/Service-KPIs korrekt bercksichtigt werden.
- Datenqualitt in logistischen Events (z.B. Fehlbuchungen) kann Root-Cause-Analysen verzerren und sollte berwacht werden.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Adjust replenishment rules and safety stock for chronic stockout SKUs | I1 | Weniger Stockouts bei kritischen Artikeln |
| Improve order accuracy and picking processes in warehouses | I2 | Hhere Service-Level und weniger Fehlerkosten |
| Remove or redesign promotions that systematisch zu Stockouts fhren | D1 | Stabilere Verfgbarkeit bei Aktionen |
| Establish joint Commercial-Supply Chain reviews for stockout hotspots | O2 | Bessere end-to-end Abstimmung und nachhaltigere Lsungen |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Stockout Rate %, On-Time-In-Full (OTIF) %, Order Accuracy %, Net Sales Amount with Plan/LY deltas.
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
- Stockout-Definition (z.B. nicht verfgbar zum Zeitpunkt der Nachfrage") ist klar dokumentiert und technisch abbildbar (Order Lines, Store-Inventory).
- Root-Cause-Codes (z.B. Forecast, Picking, Transport, Shelf) knnen nach und nach ergnzt werden; initial reichen Service- und Prozess-KPIs.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Service Level | Hhere on-shelf availability und OTIF | Stockout Rate %, OTIF % |
| Revenue | Weniger lost sales durch Stockouts | Umsatzentwicklung in Hotspot-Segmenten |
| Efficiency | Weniger manuelle Firefighting-Aktivitten | Anzahl Ad-hoc-Expedite / Notfallaktionen |