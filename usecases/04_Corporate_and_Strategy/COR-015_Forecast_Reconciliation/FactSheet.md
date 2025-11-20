---
id: "COR-015"
title: "Forecast Reconciliation (Bottom-Up ↔ Top-Down)"
domain: "Corporate and Strategy"
owner: "Head of Planning / FP&A"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Prescriptive"
supports_strategic_kpi: ["Revenue Growth %", "Working Capital %"]
supports_strategic_kpi_ids:
  ["sales.revenue.growth_pct", "fin.liquidity.working_capital"]
action_codes: ["SP1", "P2", "O2"]
expected_impact: "Automatically reconcile bottom-up and top-down forecasts to a single consensus forecast across Commercial, Operations and Finance, reducing bias and re-planning effort."
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
    "Forecast_Versions_Defined",
    "Consensus_Rules_Documented",
    "Plan_vs_Actual_Reconciles",
  ]
required_kpi_ids:
  [
    "sales.net_sales.amount",
    "sales.net_sales.amount.forecast",
    "sales.forecast.mape_pct",
    "sales.forecast.bias_pct",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  sales.net_sales.amount.forecast: "Net Sales Amount (Forecast)"
  sales.forecast.mape_pct: "Forecast Accuracy (MAPE %)"
  sales.forecast.bias_pct: "Forecast Bias %"
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
        - { name: "Forecast Type", type: string, role: attribute } # BottomUp/TopDown/Consensus
        - { name: "Forecast Date", type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Forecast Net Sales Amount", type: decimal, role: amount }
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
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_forecast.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_forecast.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_forecast."Forecast Date", to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Forecast Net Sales Amount": "fact_forecast[Forecast Net Sales Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Forecast Reconciliation (Bottom-Up ↔ Top-Down)

## 1. Business Goal
Reduce forecast bias and re-planning effort by reconciling bottom-up and top-down forecasts into a single consensus forecast by org, product and period.

---

## 2. Business Context
Sales, Operations und Finance erzeugen häufig unterschiedliche Forecasts: Bottom-up (z.B. auf Kunden- oder Produktniveau) und Top-down (z.B. vom Budget oder Board-Ziel).  
Dieser Misalignment führt zu endlosen Abstimmungsrunden und häufigen Re-Plans – mit negativen Effekten auf Kapazitätsplanung, Inventory und Vertrauen in Zahlen.  
Forecast Reconciliation nutzt definierte Regeln und ggf. ML/Optimierung, um Bottom-Up- und Top-Down-Informationen zusammenzuführen und einen konsistenten Consensus Forecast bereitzustellen.

---

## 3. Key Questions
- Wie stark weichen Bottom-Up- und Top-Down-Forecasts aktuell voneinander ab – nach Org, Produkt und Zeitraum?
- Welche Kombination aus beiden liefert den geringsten Fehler im Vergleich zu tatsächlichen Ergebnissen?
- Wie wirken sich unterschiedliche Reconciliation-Regeln (z.B. proportionale Anpassung, Priorisierung bestimmter Ebenen) auf MAPE und Bias aus?
- Wie verteilen wir den finalen Consensus Forecast zurück auf detaillierte Hierarchien (Org, Produkt, Kunde)?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| Net Sales Amount | Actual Net Sales | EUR |
| Net Sales Amount (Forecast) | Final Consensus Forecast Net Sales | EUR |
| Forecast Accuracy (MAPE %) | Mean absolute percentage error vs actual | % |
| Forecast Bias % | (Forecast - Actual) / Actual | % |

---

## 5. Required Attributes (Business-Level)
- Forecast Type: BottomUp, TopDown, Consensus.
- Forecast Version: Cycle/Version-ID.
- Time: Month, Quarter.
- Org: Region, Business Unit.
- Product: Category, Subcategory.

---

## 6. Segmentation & Hierarchies
- Time: Year > Quarter > Month.
- Org: Region > Business Unit.
- Product: Category > Subcategory.
- Forecast Type: BottomUp > TopDown > Consensus.

---

## 7. Scope & Assumptions
- Reconciliation-Regeln sind transparent dokumentiert (z.B. weightings, constraints).
- Nicht alle Organisationsebenen benötigen einen gesonderten Forecast-Typ – Fokus auf Haupt-Planungsebenen.
- ML- oder Optimierungs-Modelle können eingesetzt werden, müssen aber im Governance-Prozess verankert sein.

---

## 8. Data Freshness & Cadence
- Forecast-Cycle: monatlich/vierteljährlich.
- Aktualisierung: nach jedem offiziellen Forecast-Lauf.
- Ex-Post-Validation: nach Abschluss der Periode (z.B. M+1), inkl. MAPE/Bias-Berechnung.

---

## 9. Edge Cases & QA Rules
- Forecast-Versionen ohne klare Kennzeichnung von Typ/Quelle werden nicht in die Reconciliation einbezogen.
- Reconciliation muss die Summe der Forecasts auf allen Ebenen respektieren (Top-Down-Constraints).
- Starke Einzelfälle (z.B. Großaufträge) können gesondert behandelt werden, um die Modelle nicht zu verzerren.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Bottom-Up- und Top-Down-Forecasts nach Org/Produkt/Periode mit Version/Typ.
  - Actuals (Net Sales) zum Vergleich.
- Optional:
  - Weitere Treiber (z.B. Promotions, Preisänderungen) für erweiterte Modelle.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Define and apply reconciliation rules (e.g. weights BU vs TD) | SP1 | Weniger Forecast-Konflikte, schnellerer Konsens |
| Adjust planning responsibilities based on systematic bias | P2 | Bessere Forecast-Qualität, klarere Ownership |
| Integrate consensus forecast into S&OP and Finance planning tools | O2 | Weniger Re-Plans, bessere Abstimmung über Funktionen hinweg |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Forecast Quality | Weniger Bias und Fehler | MAPE %, Bias % nach Segment |
| Efficiency | Weniger Abstimmungsrunden und Re-Plans | Anzahl Re-Plan-Zyklen, Time-to-Signoff |
| Alignment | Höheres Vertrauen in Forecast als gemeinsame Wahrheit | Stakeholder-Zufriedenheit, Eskalationen |

---

## 13. Related Processes
Demand Planning (Bottom-Up) -> Target/Budget Setting (Top-Down) -> Reconciliation & Consensus -> S&OP & Finance Planning -> Actuals & Variance Analysis.

---

## 14. Insights & Learnings
Typische Lernings sind, dass bestimmte Regionen oder Produktbereiche systematischen Bias aufweisen und dass bestimmte Reconciliation-Regeln (z.B. gewichtete Kombination) deutlich bessere Forecast-Qualität liefern als rein Bottom-Up oder Top-Down.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-008 Sales Forecast Accuracy](../../01_Commercial/COM-008_Sales_Forecast_Accuracy/FactSheet.md)`  
  `[COR-011 Integrated S&OP](../COR-011_Integrated_S&OP/FactSheet.md)`  
  `[COR-010 Enterprise Performance Cockpit](../COR-010_Enterprise_Performance_Cockpit/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Head of Planning / FP&A] |
| Technical Reviewer | [Planning Analytics Lead] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first reconciliation cycles] |

---

_Last updated: 19.11.2025_

