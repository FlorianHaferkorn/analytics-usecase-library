---
id: "COM-001"
title: "Sales Performance & Growth Drivers"
domain: "Commercial"
owner: "VP Sales"
personas: ["Executive", "Sales Manager", "Business Analyst"]
impact: "High"
status: "Planned"
last_update: "DD.MM.YYYY"

strategic_kpis: ["sales.net.amount", "growth.sales.yoy.pct"]
supports_strategic_kpi_ids: ["sales.net.amount", "growth.sales.yoy.pct"]

action_codes: ["ACT-Pricing-01", "ACT-Inventory-01", "ACT-Promo-01"]
expected_impact: "Identify growth gaps, price-volume-mix drivers, regional underperformance; enable targeted interventions."

reporting_level: "Tactical"
analytics_stage: "Descriptive, Diagnostic, Prescriptive-ready"
maturity: "v1"

segments: ["Region", "Channel", "Product", "Customer Segment"]
filters_default: ["Date: Monthly", "Channel: All", "Region: All"]
---

## 1. Business Context & Problem
Sales performance is fragmented across regions, channels, and product lines. Variances are not consistently decomposed (price, volume, mix), and corrective actions are reactive instead of targeted. Leadership lacks a unified, actionable view.

## 2. Goals & Success Criteria
- Detect sales deviations early.
- Understand growth drivers (price, volume, mix).
- Identify underperforming regions/channels/products.
- Enable prescriptive actions via Action Codes.

## 3. Target Users & Decisions
- **Executive:** Growth outlook, regional performance signals.
- **Manager:** Channel mix, product performance, corrective measures.
- **Analyst:** Detailed drilldowns, scenario validation.

## 4. Key Questions
- What drives sales variance (Price/Volume/Mix)?
- Which regions/channels/products are underperforming?
- Welche Maßnahmen (Action Codes) sind sinnvoll?

## 5. Risks & Constraints
- Data latency may impact trend accuracy.
- Incorrect product hierarchy leads to false attributions.
- Missing promotional flags → misinterpreted mix effects.

## 6. Scenarios (3–30–300)
- **3 Sekunden:** KPI Cards (Sales, ΔYoY, ΔMoM, Mix, Price Index)
- **30 Sekunden:** Regional/Channel/Category Rankings (horizontal bar)
- **300 Sekunden:** Product-level deep dive + Action Code triggers
