---
id: "OPS-016"
title: "Bottleneck & Throughput Analysis (TOC)"
domain: "Operational Efficiency"
owner: "Head of Operations / Plant Manager"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["OEE %", "Productivity %"]
supports_strategic_kpi_ids:
  ["ops.oee.pct", "ops.performance.pct"]
action_codes: ["M2", "L2", "SP1"]
expected_impact: "Identify and manage production bottlenecks to increase overall throughput without immediate CAPEX investments."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Site>Line",
    "Asset.Family>Asset",
    "Time.Year>Month>Week>Day",
  ]
filters_default: ["Time: Last 3M", "Org: All"]
qa_asserts: ["Asset_ID_Consistent", "Routing_Defined"]
required_kpi_ids:
  [
    "ops.oee.pct",
    "ops.performance.pct",
    "ops.produced_units.qty",
  ]
required_kpis:
  ops.oee.pct: "Overall Equipment Effectiveness (OEE) %"
  ops.performance.pct: "Performance %"
  ops.produced_units.qty: "Produced Units Qty"
data_requirements:
  facts:
    - name: fact_production
      grain: production_run
      primary_key: [RunID]
      required_columns:
        - { name: RunID, type: string, role: attribute }
        - { name: AssetID, type: string, role: attribute }
        - { name: "Produced Units Qty", type: decimal, role: quantity }
        - { name: "Good Units Qty", type: decimal, role: quantity }
        - { name: "Run Start", type: datetime, role: date_key }
        - { name: "Run End", type: datetime, role: helper }
    - name: fact_mes_oee
      grain: asset_day
      primary_key: [AssetID, Date]
      required_columns:
        - { name: AssetID, type: string, role: attribute }
        - { name: Date, type: date, role: date_key }
        - { name: "OEE %", type: decimal, role: attribute }
        - { name: "Performance %", type: decimal, role: attribute }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Site, type: string }
    - name: dim_asset
      grain: asset
      primary_key: [AssetID]
      required_columns:
        - { name: "Asset Family", type: string }
        - { name: "Line", type: string }
  relationships:
    - { from: fact_production.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
    - { from: fact_mes_oee.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
model_mapping:
  "Produced Units Qty": "fact_production[Produced Units Qty]"
  "Good Units Qty": "fact_production[Good Units Qty]"
  "OEE %": "fact_mes_oee[OEE %]"
  "Performance %": "fact_mes_oee[Performance %]"
  "Asset": "dim_asset[AssetID]"
  "Org": "dim_org[OrgID]"
---

# Bottleneck & Throughput Analysis (TOC) - Business Factsheet

## 1. Summary
- **Business Goal:** Increase overall production throughput and shorten lead times by identifying and managing bottleneck resources according to the Theory of Constraints.
- **Target Audience:** Head of Operations / Plant Manager
- **Business Priority:** High
- **Expected Impact:** Identify and manage production bottlenecks to increase overall throughput without immediate CAPEX investments.

## 2. Core Questions
- Welche Anlage oder Linie ist der aktuelle Engpass im betrachteten Wertstrom?
- Wie stabil ist dieser Engpass ber Zeit - oder wandert er zwischen Ressourcen?
- Welche Manahmen (z.B. Schichtanpassung, Setup-Reduktion, Priorisierung) erhhen den Durchsatz am Engpass am strksten?
- Wie wirken sich Engpassmanahmen auf Gesamt-Output, OEE und Lieferzeiten aus?

## 3. KPI Set (Business View)
| KPI | Definition | Unit |
|-----|------------|------|
| OEE % | Availability * Performance * Quality | % |
| Performance % | Actual Output / Theoretical Output | % |
| Produced Units Qty | Total units produced per asset/period | units |
| Good Units Qty | Good units produced (excl. scrap) per asset/period | units |

## 4. Business Logic & Thresholds
- Datenlcken bei Produktionsmengen oder OEE knnen Engpassanalyse verflschen; Qualittschecks sind ntig.
- Engpass kann sich bei greren Vernderungen (z.B. Produktmix, Nachfrage, CAPEX) verschieben und sollte regelmig neu bestimmt werden.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Elevate capacity at bottleneck resources (shifts, staffing) | M2 | Higher throughput, reduced backlog |
| Reduce setup and changeover on bottleneck lines | L2 | Mehr effektive Produktionszeit, weniger Micro-Stops |
| Re-sequence production to prioritize bottleneck utilization | SP1 | Krzere Durchlaufzeiten und stabilere Auslastung |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Overall Equipment Effectiveness (OEE) %, Performance %, Produced Units Qty with Plan/LY deltas.
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
- Wertstrom-Definition (Sequenz der Anlagen) ist bekannt; Engpassanalyse erfolgt pro Wertstrom.
- CAPEX-Beschrnkungen bedeuten, dass vorrangig Prozess- und Planungsmanahmen statt neuer Anlagen betrachtet werden.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Throughput | Hherer Output ohne sofortige CAPEX-Erhhung | Produced/Good Qty per period |
| Lead Time | Krzere Durchlaufzeiten im Wertstrom | Lead Time (Prozesssicht) |
| Cost | Bessere Fixkostendegression, geringere Stckkosten | Unit Cost, OEE |