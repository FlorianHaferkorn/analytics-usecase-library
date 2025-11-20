---
id: "COR-014"
title: "Integrated Margin Bridge (P&L Driver Tree)"
domain: "Corporate and Strategy"
owner: "CFO / Head of Controlling"
impact: "Very High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Strategic"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Gross Margin %", "EBITDA Margin %"]
supports_strategic_kpi_ids: ["margin.gm.pct", "profit.ebitda_margin"]
action_codes: ["SP1", "SP2", "M3", "O2"]
expected_impact: "Provide a board-ready, fully reconciled driver tree from Net Sales to Gross Margin, EBITDA and Net Result across price, mix, volume, COGS, logistics, supplier terms and FX."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>BusinessUnit",
    "Time.Year>Quarter>Month",
    "Product.Category>Subcategory",
  ]
filters_default: ["Time: YTD", "Org: All"]
qa_asserts: ["P&L_Reconciles", "Bridge_Fully_Explained"]
required_kpi_ids:
  [
    "sales.net_sales.amount",
    "margin.gm.amount",
    "margin.gm.pct",
    "profit.ebitda_margin",
    "sales.net_sales.delta_amount.ly",
    "sales.pvm.price_effect.amount",
    "sales.pvm.volume_effect.amount",
    "sales.pvm.mix_effect.amount",
    "cost.cogs.amount",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  margin.gm.amount: "Gross Margin Amount"
  margin.gm.pct: "Gross Margin %"
  profit.ebitda_margin: "EBITDA Margin %"
  sales.net_sales.delta_amount.ly: "Δ Net Sales Amount vs LY"
  sales.pvm.price_effect.amount: "Price Effect Amount"
  sales.pvm.volume_effect.amount: "Volume Effect Amount"
  sales.pvm.mix_effect.amount: "Mix Effect Amount"
  cost.cogs.amount: "COGS Amount"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "COGS Amount", type: decimal, role: amount }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
    - name: fact_pnl
      grain: org_period_pnl
      primary_key: [OrgID, Period, PnLLine]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: PnLLine, type: string, role: attribute }
        - { name: "Amount", type: decimal, role: amount }
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
    - { from: fact_pnl.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_pnl.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "COGS Amount": "fact_sales[COGS Amount]"
  "PnL Amount": "fact_pnl[Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Integrated Margin Bridge (P&L Driver Tree)

## 1. Business Goal
Provide a fully reconciled P&L driver tree that explains changes from Net Sales to Gross Margin and EBITDA by price, volume, mix, COGS and other drivers, enabling management to focus on the most impactful levers.

---

## 2. Business Context
Im Alltag sehen Management und Fachbereiche oft nur aggregierte Margenkennzahlen, ohne klare Erklärung, welche Treiber (Preis, Mix, Volumen, COGS, FX, Overheads) die größte Rolle spielen.  
Unterschiedliche Quellen (Sales-Dashboards, Finance-Reports, Controlling-Analysen) liefern unterschiedliche Antworten und erschweren eine gemeinsame Diskussion.  
Dieser Use Case baut eine integrierte Margin Bridge auf, die P&L-Treiber konsistent erklärt und an die Sales-PVM-Analysen anbindet.

---

## 3. Key Questions
- Wie viel des Margen- und Ergebnis-Changes ist auf Preis-, Volumen- und Mixeffekte zurückzuführen?
- Welchen Beitrag leisten COGS, Logistikkosten, Rabatte und FX zur Veränderung von GM % und EBITDA?
- Wie verteilen sich die Treiber auf Regionen, Business Units und Produktkategorien?
- Welche Treiber sind dauerhaft (strukturell) und welche nur temporär (z.B. Einmalaufwendungen)?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| Net Sales Amount | Sales revenue | EUR |
| Gross Margin Amount | Net Sales - COGS | EUR |
| Gross Margin % | Gross Margin / Net Sales | % |
| EBITDA Margin % | EBITDA / Net Sales | % |
| Δ Net Sales Amount vs LY | Net Sales - Net Sales LY | EUR |
| Price Effect Amount | PVM price component | EUR |
| Volume Effect Amount | PVM volume component | EUR |
| Mix Effect Amount | PVM mix component | EUR |

---

## 5. Required Attributes (Business-Level)
- Time: Year, Quarter, Month.
- Org: Region, Business Unit.
- Product: Category, Subcategory (für PVM).
- P&L Line: Net Sales, COGS, OpEx, EBITDA, Net Result.

---

## 6. Segmentation & Hierarchies
- Time: Year > Quarter > Month.
- Org: Region > Business Unit.
- Product: Category > Subcategory.
- P&L: Revenue > GM > EBITDA > Net Result.

---

## 7. Scope & Assumptions
- PVM-Logik ist bereits in COM-004/007 etabliert und wird hier wiederverwendet.
- Mapping zwischen Sales- und Finance-Sicht (z.B. Aggregationslogik, Währungen) ist definiert und abgestimmt.
- Overhead- und FX-Effekte können als separate Bridge-Blöcke oder Teil von EBITDA erläutert werden.

---

## 8. Data Freshness & Cadence
- Monatliche Aktualisierung synchron mit Financial Close.
- Optional wöchentliche bzw. Rolling-Views für Net Sales und GM.

---

## 9. Edge Cases & QA Rules
- Bridge muss auf Gesamtunternehmensebene zu offiziellen P&L-Zahlen (Revenue, GM, EBITDA, Net Result) vollständig reconciliert sein.
- Einmalige Sondereffekte (z.B. Impairments, M&A) werden gesondert ausgewiesen.
- FX-Effekte werden konsistent zu Finance-Definitionen behandelt.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Sales (Net Sales, COGS) nach Org/Produkt/Periode.
  - P&L-Faktentabelle mit mindestens Net Sales, COGS, EBITDA nach Org/Periode.
- Optional:
  - Detaillierte OpEx- und FX-Daten für tiefergehende Bridges.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Fokus auf Treiber mit höchstem Margenimpact (z.B. Preis vs Mix vs COGS) | SP1 | Effizientere Maßnahmenplanung, schnellere Ergebnisverbesserung |
| Ableitung von Initiativen aus Treiberanalyse (z.B. COGS-Programme, Mix-Optimierung) | SP2 | Nachhaltige Verbesserung der Profitabilität |
| Anpassung von Zielvorgaben und Bonusmodellen entlang der Treiber | O2 | Besser ausgerichtete Incentives |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Transparency | Klare, geteilte Sicht auf Ergebnis-Treiber | Anzahl offener Reconciliation-Fragen ↓ |
| Profitability | Schnellere Identifikation und Umsetzung von Profit-Programmen | GM %, EBITDA Margin vs Plan/LY |

---

## 13. Related Processes
Financial Closing -> Management Reporting -> Margin Review -> Initiative Design & Tracking.

---

## 14. Insights & Learnings
Die integrierte Bridge zeigt oft, dass ein Großteil der Ergebnisabweichung auf wenige Treiber entfällt (z.B. Preis- und Mixeffekte in bestimmten Regionen oder COGS-Verschiebungen bei einzelnen Produktkategorien), während andere Effekte vernachlässigbar sind. Dies hilft, Initiativen zu fokussieren.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-004 Price-Volume-Mix Bridge](../../01_Commercial/COM-004_Price_Volume_Mix_Bridge/FactSheet.md)`  
  `[COM-007 Price-Volume-Mix Bridge (Portfolio & Strategic View)](../../01_Commercial/COM-007_Price_Volume_Mix_Bridge/FactSheet.md)`  
  `[COR-005 Profitability Overview](../COR-005_Profitability_Overview/FactSheet.md)`  
  `[COR-010 Enterprise Performance Cockpit](../COR-010_Enterprise_Performance_Cockpit/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [CFO / Head of Controlling] |
| Technical Reviewer | [Finance BI Lead] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first Board reviews] |

---

_Last updated: 19.11.2025_

