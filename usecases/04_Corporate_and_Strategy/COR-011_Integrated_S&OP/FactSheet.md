---
id: "COR-011"
title: "Integrated Sales & Operations Planning (S&OP)"
domain: "Corporate and Strategy"
owner: "COO / Head of S&OP"
impact: "Very High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi:
  [
    "Revenue Growth %",
    "Gross Margin %",
    "Working Capital %",
    "CCC Days",
  ]
supports_strategic_kpi_ids:
  [
    "sales.revenue.growth_pct",
    "margin.gm.pct",
    "fin.liquidity.working_capital",
    "ops.working_capital.ccc.days",
  ]
action_codes: ["SP1", "P2", "W1", "O2"]
expected_impact: "Align demand, supply and financial plans into one consensus plan; reduce forecast error, inventory and stockouts while protecting margin."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>BusinessUnit",
    "Time.Year>Quarter>Month",
    "Product.Category>Subcategory",
  ]
filters_default: ["Time: Next 12M", "Org: All"]
qa_asserts:
  [
    "Forecast_Version_Frozen",
    "Supply_Capacity_Complete",
    "Plan_vs_Actual_Reconciles",
  ]
required_kpi_ids:
  [
    "sales.net_sales.amount",
    "sales.net_sales.amount.forecast",
    "sales.forecast.mape_pct",
    "sales.forecast.bias_pct",
    "ops.capacity.utilization.pct",
    "ops.inventory.days",
    "ops.inventory.turnover",
    "ops.stockout.pct",
    "fin.liquidity.working_capital",
    "ops.working_capital.ccc.days",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  sales.net_sales.amount.forecast: "Net Sales Amount (Forecast)"
  sales.forecast.mape_pct: "Forecast Accuracy (MAPE %)"
  sales.forecast.bias_pct: "Forecast Bias %"
  ops.capacity.utilization.pct: "Capacity Utilization %"
  ops.inventory.days: "Inventory Days on Hand (DIO)"
  ops.inventory.turnover: "Inventory Turnover"
  ops.stockout.pct: "Stockout Rate %"
  fin.liquidity.working_capital: "Working Capital %"
  ops.working_capital.ccc.days: "Cash Conversion Cycle (Days)"
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
    - name: fact_forecast
      grain: forecast_line
      primary_key: [ForecastLineID]
      required_columns:
        - { name: "Forecast Version", type: string, role: attribute }
        - { name: "Forecast Date", type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Forecast Net Sales Amount", type: decimal, role: amount }
        - { name: "Forecast Units Qty", type: decimal, role: quantity }
    - name: fact_capacity
      grain: org_resource_period
      primary_key: [OrgID, ResourceID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ResourceID, type: string, role: attribute }
        - { name: "Available Hours", type: decimal, role: amount }
        - { name: "Planned Load Hours", type: decimal, role: amount }
    - name: fact_inventory
      grain: org_product_period
      primary_key: [OrgID, ProductID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Inventory Amount", type: decimal, role: amount }
        - { name: "Inventory Units Qty", type: decimal, role: quantity }
    - name: fact_service_level
      grain: org_product_period
      primary_key: [OrgID, ProductID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Order Lines Total", type: int, role: quantity }
        - { name: "Order Lines Stockout", type: int, role: quantity }
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
        - { name: BusinessUnit, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
  relationships:
    - {
        from: fact_sales.Date,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_sales.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_sales.ProductID,
        to: dim_product.ProductID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_forecast.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_forecast.ProductID,
        to: dim_product.ProductID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_forecast."Forecast Date",
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_capacity.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_capacity.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_inventory.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_inventory.ProductID,
        to: dim_product.ProductID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_inventory.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_service_level.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_service_level.ProductID,
        to: dim_product.ProductID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_service_level.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Forecast Net Sales Amount": "fact_forecast[Forecast Net Sales Amount]"
  "Available Capacity Hours": "fact_capacity[Available Hours]"
  "Planned Load Hours": "fact_capacity[Planned Load Hours]"
  "Inventory Amount": "fact_inventory[Inventory Amount]"
  "Inventory Units Qty": "fact_inventory[Inventory Units Qty]"
  "Order Lines Total": "fact_service_level[Order Lines Total]"
  "Order Lines Stockout": "fact_service_level[Order Lines Stockout]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Integrated Sales & Operations Planning (S&OP)

## 1. Business Goal
Create a single, integrated Sales & Operations Plan that aligns demand, supply and financials, reducing forecast error, inventory and stockouts while protecting gross margin and cash.

---

## 2. Business Context
In many organizations, demand planning, production planning and finance planning are still performed in Silos – with separate tools, calendars and ownership.  
This leads to recurring firefighting: shortages in peak periods, overstocks after promotions, frequent re-planning and missed financial commitments.  
Integrated S&OP connects demand forecasts, capacity and inventory targets with margin and working-capital implications, and provides one consensus plan per cycle.

---

## 3. Key Questions
- How does the demand forecast compare to recent actuals by region, channel and product family?
- Where do we see structural over- or under-forecasting (bias) by planner, segment or horizon?
- Do we have sufficient capacity to serve the planned demand and promotions without creating bottlenecks?
- Sind Inventory Targets (Safety Stock, DIO) konsistent mit Service-Level und CCC-Zielen?
- Wie stark weichen Ist-Produktion, Auslieferung und Umsatz vom S&OP-Consensus-Plan ab?
- Welche S&OP-Entscheidungen haben den größten Impact auf GM % und Working Capital?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| Net Sales Amount | Sum of invoiced net sales | EUR |
| Net Sales Amount (Forecast) | Forecasted Net Sales per period | EUR |
| Forecast Accuracy (MAPE %) | Mean absolute percentage error vs actual net sales | % |
| Forecast Bias % | (Forecast - Actual) / Actual | % |
| Capacity Utilization % | Planned Load Hours / Available Hours | % |
| Inventory Days (DIO) | Inventory / COGS * Days in Period | days |
| Inventory Turnover | COGS / Avg Inventory | ratio |
| Stockout Rate % | Stockout Order Lines / Total Order Lines | % |
| Working Capital % | (AR + Inventory - AP) / Net Sales | % |
| CCC Days | DSO + DIO - DPO | days |

---

## 5. Required Attributes (Business-Level)
- Time: Month (optionally Week) for planning horizon.
- Org: Region, Business Unit, Site/Plant (for Capacity & Inventory).
- Product: Category, Subcategory, optionally Family.
- Forecast attributes: Version, Scenario (Base/Best/Worst), Horizon.
- Capacity: Resource/Line, available hours, planned load.
- Service: Order Lines, Stockout Flag.

---

## 6. Segmentation & Hierarchies
- Time: Year > Quarter > Month (optional: Week).
- Org: Region > Business Unit > Site.
- Product: Category > Subcategory > Planning Family.
- Forecast: Scenario (Consensus/Base/Stretch) > Version.

---

## 7. Scope & Assumptions
- S&OP is focused on mid-term horizon (3–18 months); kurzfristige Detailsteuerung erfolgt in operativen OPS-Use-Cases.
- Forecasts are versioned and frozen per cycle; ex-post Änderungen werden nicht rückwirkend überschrieben.
- Capacity is modeled auf aggregiertem Level (Lines/Workcenters), nicht auf Schicht-/Mitarbeiter-Ebene.
- Inventory Targets und Service-Level-Vorgaben sind zentral definiert und pro Segment anpassbar.
- Finanzielle KPIs (GM %, Working Capital, CCC) werden mit Finance abgestimmt (gleiche Periodenschnitte und Definitionslogik).

---

## 8. Data Freshness & Cadence
- S&OP Cycle: monatlich (z.B. M+1 bis M+18), mit Roll-Vorhersage.
- Demand Forecast: mindestens monatliches Update; operative Aktualisierung ggf. häufiger.
- Capacity und Inventory: wöchentlich oder monatlich aktualisiert, abhängig von Volatilität.
- Finanz- und Working-Capital-KPIs: synchron mit Monatsabschluss oder nachlaufend.

---

## 9. Edge Cases & QA Rules
- Forecast-Versionen ohne Freeze-Date werden im S&OP-Cockpit nicht als Basis für Accuracy/Bias verwendet.
- Kapazitätsszenarien (z.B. Überstunden, Zusatzschichten) müssen gekennzeichnet werden, um Planbarkeit zu bewerten.
- Promotions mit Sonderlogik werden entweder konsistent in Forecast und Supply abgebildet oder ausgeschlossen.
- Inventory- und Service-Level-Daten benötigen konsistente Org-/Produkt-Schlüssel mit Sales- und Finance-Daten.
- Reconciliation-Regeln zwischen S&OP-Plan und Finance-Plan müssen dokumentiert und überwacht werden.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Historische Net Sales und Forecast-Daten nach Org/Produkt/Periode.
  - Aggregierte Kapazitäts- und Auslastungsdaten je Site/Resource.
  - Inventory-Bestände und -Werte je Org/Produkt/Periode.
  - Service-Level-Proxy (z.B. Stockout Order Lines).
- Optional:
  - Promotions- und Kampagnenkalender.
  - Detaillierte BOM-/Routing-Informationen für Kapazitätsengpässe.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Adjust production plan or capacity to close major gaps between demand and supply | P2 | Weniger Bottlenecks, stabilere Lieferfähigkeit |
| Re-align promotion and demand plans to realistic capacity and inventory constraints | SP1 | Reduktion von Überbeständen und Fehlmengen |
| Update inventory targets and safety stock by segment | W1 | Niedrigere DIO bei stabilem Service-Level |
| Trigger Finance re-plan when major S&OP shifts occur | O2 | Bessere Abstimmung zwischen operativem Plan und P&L/WC-Plan |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Service Level | Fewer stockouts during peak demand | Stockout Rate %, OTIF |
| Efficiency | Reduzierte Re-Planning-Schleifen und Firefighting | Anzahl Ad-hoc-Replans |
| Liquidity | Besser ausbalancierte Inventory-Levels vs Service | DIO, Working Capital % |
| Profitability | Bessere GM %, da Kapazitäts- und Promo-Entscheidungen früh abgestimmt werden | GM %, EBITDA vs Plan |

---

## 13. Related Processes
Demand Review -> Supply Review -> Pre-S&OP Meeting -> Executive S&OP Meeting -> Plan Lock & Communication.

---

## 14. Insights & Learnings
Typische Learnings umfassen systematische Forecast-Biases in bestimmten Segmenten, Kapazitätsengpässe, die regelmäßig zu verspäteten Lieferungen führen, sowie Inventory-Strategien, die Cash unnötig binden oder Service-Level gefährden.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-008 Sales Forecast Accuracy](../../01_Commercial/COM-008_Sales_Forecast_Accuracy/FactSheet.md)`  
  `[OPS-001 Cash Conversion Cycle](../../02_Operational_Efficiency/OPS-001_Cash_Conversion_Cycle/FactSheet.md)`  
  `[OPS-004 Replenishment Optimization](../../02_Operational_Efficiency/OPS-004_Replenishment_Optimization/FactSheet.md)`  
  `[OPS-010 Replenishment & Safety Stock](../../02_Operational_Efficiency/OPS-010_Replenishment_and_Safety_Stock/FactSheet.md)`  
  `[COR-001 Working Capital & CCC](../COR-001_Project_ROI_and_Benefit_Tracking/FactSheet.md)`  
  `[COR-010 Enterprise Performance Cockpit](../COR-010_Enterprise_Performance_Cockpit/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [COO / Head of S&OP] |
| Technical Reviewer | [Lead S&OP Planner / BI Lead] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first S&OP cycles] |

---

_Last updated: 19.11.2025_

