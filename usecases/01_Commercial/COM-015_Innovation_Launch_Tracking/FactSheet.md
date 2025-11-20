---
id: "COM-015"
title: "Innovation Launch Tracking"
domain: "Commercial"
owner: "Head of Innovation / Category Management"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Innovation Rate %"]
supports_strategic_kpi_ids:
  ["sales.revenue.growth_pct", "people.innovation_rate.pct"]
action_codes: ["I2", "P2", "SP1"]
expected_impact: "Track distribution, offtake and repeat for new products to improve launch success and de-list weak innovations faster."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>Channel",
    "Product.Category>Subcategory>SKU",
    "Time.Year>Quarter>Month",
  ]
filters_default: ["Time: Last 24M", "Org: All"]
qa_asserts: ["Innovation_Flag_Consistent", "Lifecycle_Stage_Defined"]
required_kpi_ids:
  [
    "sales.net_sales.amount",
    "margin.gm.pct",
    "people.innovation_rate.pct",
    "people.new_product_share",
    "prod.lifecycle.new_share.pct",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  margin.gm.pct: "Gross Margin %"
  people.innovation_rate.pct: "Innovation Rate %"
  people.new_product_share: "New Product Share"
  prod.lifecycle.new_share.pct: "New Product Share % in Lifecycle"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Is New Product", type: bool, role: indicator }
    - name: fact_product_lifecycle
      grain: product_period
      primary_key: [ProductID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Lifecycle Stage", type: string, role: attribute }
        - { name: "New Flag", type: bool, role: indicator }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Quarter, type: int }
        - { name: Month, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Channel, type: string }
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
    - { from: fact_product_lifecycle.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_product_lifecycle.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Lifecycle Stage": "fact_product_lifecycle[Lifecycle Stage]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Innovation Launch Tracking

## 1. Business Goal
Track the performance of new product launches from distribution to trial and repeat in order to focus investment on successful innovations and de-list weak launches faster.

---

## 2. Business Context
Innovation is a key driver of growth in FMCG, Retail and Pharma, aber viele Launches erreichen nie kritische Masse.  
Oft fehlt eine durchgängige Sicht von Distribution, Erstkäufen, Wiederkaufraten und Margenbeitrag über die ersten 12–24 Monate nach Launch.  
Dieser Use Case verknüpft Innovationskennzahlen mit Sales- und Lifecycle-Daten und macht sichtbar, welche Launches skalierbar sind und welche Ressourcen binden.

---

## 3. Key Questions
- Welche Innovationen liefern den größten Umsatz- und Margenbeitrag in den ersten 12–24 Monaten?
- Wie entwickeln sich Distribution, Trial und Repeat über Regionen, Kanäle und Segmente?
- Welche Launches sind „Slow Movers“ mit geringer Wiederkaufsrate – und sollten früher angepasst oder gestrichen werden?
- Wie trägt Innovation insgesamt zu Revenue Growth % und Innovation Rate % bei?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| Net Sales Amount | Sales revenue from new products | EUR |
| Gross Margin % | (Net Sales - COGS) / Net Sales | % |
| Innovation Rate % | Anteil Umsatz aus Innovationen | % |
| New Product Share | Umsatzanteil neuer Produkte an Gesamtumsatz | % |
| New Product Share % in Lifecycle | Anteil „New“-Stufe an Produkt-Lifecycle | % |

---

## 5. Required Attributes (Business-Level)
- Product: Category, Subcategory, SKU, Innovation-Flag, Lifecycle Stage.
- Org: Region, Channel.
- Time: Year, Quarter, Month seit Launch.

---

## 6. Segmentation & Hierarchies
- Product: Category > Subcategory > SKU.
- Org: Region > Channel.
- Time: Year > Quarter > Month; zusätzlich „Months since Launch“ als Analyseachse.

---

## 7. Scope & Assumptions
- „Innovation“ wird über ein Produktmerkmal (z.B. Launchjahr, Launchflag) definiert; Definition sollte zentral dokumentiert sein.
- Lifecycle-Stufen (New, Growth, Mature, Decline) sind mit dem Product Lifecycle Use Case abgestimmt.
- Launchperformance umfasst i.d.R. 12–24 Monate; darüber hinaus geht das Produkt in Standard-Analysen ein.

---

## 8. Data Freshness & Cadence
- Sales: täglich/wöchentlich, im Use Case auf Monats-/Quartalsebene verdichtet.
- Lifecycle-Stufen: mindestens monatliches Update.
- Reporting: monatlich/vierteljährlich für Innovation Boards und Category-Reviews.

---

## 9. Edge Cases & QA Rules
- Produkte mit verspätetem Rollout (z.B. schrittweise Länder-/Channel-Einführung) werden klar gekennzeichnet.
- Outlier-Effekte (z.B. Einmal-Großaufträge) sollten separat betrachtet werden.
- Änderungen in der Innovatonsdefinition (z.B. Änderungsjahr) werden versioniert dokumentiert.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Sales nach Produkt/Org/Periode mit Innovation-Flag.
  - Lifecycle-Stufe pro Produkt/Periode.
- Optional:
  - Distribution- und Placement-Daten, Consumer-Panel für Trial/Repeat.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Scale successful launches schneller in Regionen/Kanälen mit gutem Fit | I2 | Mehr Umsatzanteil aus erfolgreichen Innovationen |
| Stop or redesign weak launches basierend auf klaren CLV-/Margen-Schwellen | P2 | Reduzierte Komplexität und Marketingverschwendung |
| Align innovation pipeline with categories and segments with highest response | SP1 | Besser fokussierte Innovations-Roadmap |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Growth | Höherer Umsatzanteil aus erfolgreichen Innovationen | Innovation Rate %, New Product Share |
| Profitability | Reduktion unprofitabler Launches | GM % von Innovationskohorten |
| Efficiency | Bessere Allokation von F&E- und Launchbudget | Launch ROI, Anteil skalierter vs. eingestellter Innovationen |

---

## 13. Related Processes
Innovation Funnel & Stage-Gate -> Launch Planning -> Distribution & Activation -> Post-Launch Review -> Portfolio Decisions.

---

## 14. Insights & Learnings
Typische Learnings: Ein kleiner Teil der Launches liefert den Großteil des Innovationswachstums, während viele Launches nur Komplexität ohne nachhaltigen Beitrag erzeugen. Wiederkaufsraten und regionale Performance sind oft sehr unterschiedlich – Daten helfen, dies früh zu erkennen.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-011 Innovation Revenue Contribution](../COM-011_Innovation_Revenue_Contribution/FactSheet.md)`  
  `[CST-002 Product Lifecycle Performance](../../03_Customer_and_Market/CST-002_Product_Lifecycle_Performance/FactSheet.md)`  
  `[COR-010 Enterprise Performance Cockpit](../../04_Corporate_and_Strategy/COR-010_Enterprise_Performance_Cockpit/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Head of Innovation / Category Management] |
| Technical Reviewer | [Innovation Analytics Lead] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first launch cohorts] |

---

_Last updated: 19.11.2025_

