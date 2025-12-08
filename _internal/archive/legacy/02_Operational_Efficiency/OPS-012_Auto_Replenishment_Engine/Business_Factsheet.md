---
id: "OPS-012"
title: "Auto-Replenishment Engine"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Demand Planning"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Working Capital %", "CCC Days", "Service Level %"]
supports_strategic_kpi_ids:
  ["fin.liquidity.working_capital", "ops.working_capital.ccc.days", "ops.otif.pct"]
action_codes: ["W1", "P2", "O2"]
expected_impact: "Automate replenishment decisions by proposing optimal order quantities and timings per SKU/location, balancing service level and working capital."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>Site",
    "Product.Category>Subcategory>SKU",
    "Time.Year>Month>Week",
  ]
filters_default: ["Time: Next 12W", "Org: All"]
qa_asserts:
  [
    "Forecast_Version_Frozen",
    "LeadTime_Defined",
    "MinMax_Policy_Documented",
  ]
required_kpi_ids:
  [
    "ops.inventory.days",
    "ops.inventory.turnover",
    "ops.stockout.pct",
    "ops.replenishment.adherence.pct",
    "ops.order_accuracy.pct",
    "ops.otif.pct",
    "sales.net_sales.amount",
    "sales.net_sales.amount.forecast",
    "sales.forecast.mape_pct",
  ]
required_kpis:
  ops.inventory.days: "Inventory Days on Hand (DIO)"
  ops.inventory.turnover: "Inventory Turnover"
  ops.stockout.pct: "Stockout Rate %"
  ops.replenishment.adherence.pct: "Replenishment Plan Adherence %"
  ops.order_accuracy.pct: "Order Accuracy %"
  ops.otif.pct: "On-Time-In-Full (OTIF) %"
  sales.net_sales.amount: "Net Sales Amount"
  sales.net_sales.amount.forecast: "Net Sales Amount (Forecast)"
  sales.forecast.mape_pct: "Forecast Accuracy (MAPE %)"
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
        - { name: "Units Qty", type: decimal, role: quantity }
    - name: fact_forecast
      grain: forecast_line
      primary_key: [ForecastLineID]
      required_columns:
        - { name: "Forecast Version", type: string, role: attribute }
        - { name: "Forecast Date", type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Forecast Units Qty", type: decimal, role: quantity }
    - name: fact_inventory
      grain: org_product_day
      primary_key: [OrgID, ProductID, Date]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "On Hand Units Qty", type: decimal, role: quantity }
    - name: fact_replenishment_plan
      grain: org_product_day
      primary_key: [OrgID, ProductID, Date]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Planned Order Units Qty", type: decimal, role: quantity }
        - { name: "Actual Order Units Qty", type: decimal, role: quantity }
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
        - { name: Site, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
        - { name: "Lead Time Days", type: int }
        - { name: "Min Stock Units", type: decimal }
        - { name: "Max Stock Units", type: decimal }
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_forecast.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_forecast.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_forecast."Forecast Date", to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_inventory.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_inventory.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_inventory.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_replenishment_plan.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_replenishment_plan.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_replenishment_plan.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Forecast Units Qty": "fact_forecast[Forecast Units Qty]"
  "On Hand Units Qty": "fact_inventory[On Hand Units Qty]"
  "Planned Order Units Qty": "fact_replenishment_plan[Planned Order Units Qty]"
  "Actual Order Units Qty": "fact_replenishment_plan[Actual Order Units Qty]"
  "Order Lines Total": "fact_service_level[Order Lines Total]"
  "Order Lines Stockout": "fact_service_level[Order Lines Stockout]"
  "Order Lines OTIF": "fact_service_level[Order Lines OTIF]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Auto-Replenishment Engine - Business Factsheet

## 1. Summary
- **Business Goal:** Automate replenishment decisions by proposing optimal order quantities and timings per SKU/location to meet target service levels while minimizing inventory days and working capital.
- **Target Audience:** Head of Supply Chain / Demand Planning
- **Business Priority:** High
- **Expected Impact:** Automate replenishment decisions by proposing optimal order quantities and timings per SKU/location, balancing service level and working capital.

## 2. Core Questions
- Welche SKUs/Standorte sind aktuell ber- bzw. unterversorgt im Vergleich zum Zielbestand?
- Wie gut treffen unsere bisherigen Replenishment-Regeln die definierte Service-Level-Zielgre?
- Welche Bestellvorschlge ergeben sich aus einem datengetriebenen Algorithmus (z.B. (R,Q)-Policy, Safety-Stock-Formeln)?
- Wo weichen Planner-Entscheidungen systematisch von den Vorschlgen ab - und mit welchen Effekten auf Service und Bestnde?

## 3. KPI Set (Business View)
| KPI | Definition | Unit |
|-----|------------|------|
| Inventory Days (DIO) | Inventory / COGS * Days in Period | days |
| Inventory Turnover | COGS / Avg Inventory | ratio |
| Stockout Rate % | Stockout Order Lines / Total Order Lines | % |
| Replenishment Plan Adherence % | 1 - |Actual - Planned| / Planned Orders | % |
| Order Accuracy % | Correctly fulfilled orders / Total orders | % |
| OTIF % | On-Time-In-Full deliveries / Total deliveries | % |
| Forecast Accuracy (MAPE %) | MAPE von Forecast vs Actual Units | % |

## 4. Business Logic & Thresholds
- SKUs ohne belastbare Historie oder Forecast werden mit konservativer Policy (z.B. manuelle Freigabe) behandelt.
- Negative Bestnde und fehlerhafte Buchungen werden vor der Berechnung bereinigt oder ausgeschlossen.
- Service-Level-KPI-Berechnungen werden auf definierte Zeitfenster und Segmente begrenzt (z.B. Ausschluss von Launchartikeln in den ersten Wochen).

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Implement auto-generated order proposals for defined SKU classes | W1 | Reduzierte Bestandsstreuung, weniger Stockouts |
| Adjust Min/Max and safety-stock parameters based on algorithm output | P2 | Bessere Balance zwischen DIO und Service-Level |
| Escalate exceptions (z.B. Kapazitts- oder Supplier-Limits) in S&OP-Prozess | O2 | Hhere Planbarkeit und weniger Ad-hoc-Firefighting |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Inventory Days on Hand (DIO), Inventory Turnover, Stockout Rate %, Replenishment Plan Adherence %, Order Accuracy % with Plan/LY deltas.
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
- Die Engine erzeugt Bestellvorschlge (z.B. Order Qty" je SKU/Site/Day); finale Entscheidungen liegen weiterhin beim Planner.
- Lead Times, Min/Max und Service-Level-Ziele sind zentral gepflegt und werden regelmig berprft.
- Algorithmus-Variante (z.B. klassische Safety-Stock-Formel, Croston, Machine Learning) kann je Reifegrad variieren, beeinflusst aber nicht die KPI-Logik.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Service Level | Weniger Stockouts bei kritischen SKUs | Stockout Rate %, OTIF |
| Efficiency | Weniger manuelle Dispoprozesse | Anzahl manuell disponierter SKUs, Planerzeit |
| Liquidity | Reduktion von berbestnden bei stabilen Service Levels | DIO, Inventory Turnover |