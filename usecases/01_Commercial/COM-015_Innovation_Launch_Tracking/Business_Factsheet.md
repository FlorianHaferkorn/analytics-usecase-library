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

# Innovation Launch Tracking - Business Factsheet

## 1. Summary
- **Business Goal:** Track the performance of new product launches from distribution to trial and repeat in order to focus investment on successful innovations and de-list weak launches faster.
- **Target Audience:** Head of Innovation / Category Management
- **Business Priority:** High
- **Expected Impact:** Track distribution, offtake and repeat for new products to improve launch success and de-list weak innovations faster.

## 2. Core Questions
- Welche Innovationen liefern den grten Umsatz- und Margenbeitrag in den ersten 12-24 Monaten?
- Wie entwickeln sich Distribution, Trial und Repeat ber Regionen, Kanle und Segmente?
- Welche Launches sind Slow Movers" mit geringer Wiederkaufsrate - und sollten frher angepasst oder gestrichen werden?
- Wie trgt Innovation insgesamt zu Revenue Growth % und Innovation Rate % bei?

## 3. KPI Set (Business View)
| KPI | Definition | Unit |
|-----|------------|------|
| Net Sales Amount | Sales revenue from new products | EUR |
| Gross Margin % | (Net Sales - COGS) / Net Sales | % |
| Innovation Rate % | Anteil Umsatz aus Innovationen | % |
| New Product Share | Umsatzanteil neuer Produkte an Gesamtumsatz | % |
| New Product Share % in Lifecycle | Anteil New"-Stufe an Produkt-Lifecycle | % |

## 4. Business Logic & Thresholds
- Produkte mit versptetem Rollout (z.B. schrittweise Lnder-/Channel-Einfhrung) werden klar gekennzeichnet.
- Outlier-Effekte (z.B. Einmal-Groauftrge) sollten separat betrachtet werden.
- nderungen in der Innovatonsdefinition (z.B. nderungsjahr) werden versioniert dokumentiert.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Scale successful launches schneller in Regionen/Kanlen mit gutem Fit | I2 | Mehr Umsatzanteil aus erfolgreichen Innovationen |
| Stop or redesign weak launches basierend auf klaren CLV-/Margen-Schwellen | P2 | Reduzierte Komplexitt und Marketingverschwendung |
| Align innovation pipeline with categories and segments with highest response | SP1 | Besser fokussierte Innovations-Roadmap |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Net Sales Amount, Gross Margin %, Innovation Rate %, New Product Share, New Product Share % in Lifecycle with Plan/LY deltas.
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
- Innovation" wird ber ein Produktmerkmal (z.B. Launchjahr, Launchflag) definiert; Definition sollte zentral dokumentiert sein.
- Lifecycle-Stufen (New, Growth, Mature, Decline) sind mit dem Product Lifecycle Use Case abgestimmt.
- Launchperformance umfasst i.d.R. 12-24 Monate; darber hinaus geht das Produkt in Standard-Analysen ein.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Growth | Hherer Umsatzanteil aus erfolgreichen Innovationen | Innovation Rate %, New Product Share |
| Profitability | Reduktion unprofitabler Launches | GM % von Innovationskohorten |
| Efficiency | Bessere Allokation von F&E- und Launchbudget | Launch ROI, Anteil skalierter vs. eingestellter Innovationen |