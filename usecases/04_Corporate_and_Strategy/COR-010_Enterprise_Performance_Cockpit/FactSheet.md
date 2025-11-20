---
id: "COR-010"
title: "Enterprise Performance Cockpit"
domain: "Corporate and Strategy"
owner: "CEO / CFO / COO"
impact: "Very High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Strategic"
analytics_stage: "Descriptive"
supports_strategic_kpi:
  [
    "Revenue Growth %",
    "Gross Margin %",
    "Working Capital %",
    "CCC Days",
    "Customer Retention %",
    "Headcount Efficiency",
    "ESG-Aligned Revenue %",
  ]
supports_strategic_kpi_ids:
  [
    "sales.revenue.growth_pct",
    "margin.gm.pct",
    "fin.liquidity.working_capital",
    "ops.working_capital.ccc.days",
    "crm.retention.pct",
    "hr.revenue_per_fte.amount",
    "esg.aligned_revenue.pct",
  ]
action_codes: ["SP1", "SP2", "G1", "W1"]
expected_impact: "Provide a single, board-ready view on growth, profitability, liquidity, efficiency, customer value, people and ESG to enable fact-based, cross-domain steering."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>BusinessUnit",
    "Time.Year>Quarter>Month",
    "Customer.Segment",
    "Product.Category>Subcategory",
  ]
filters_default: ["Time: Last 24M", "Org: All"]
qa_asserts: ["RI_OK", "KPI_Definitions_Aligned", "P&L_Reconciles"]
required_kpi_ids:
  [
    "sales.net_sales.amount",
    "sales.revenue.growth_pct",
    "margin.gm.pct",
    "profit.ebitda_margin",
    "fin.liquidity.working_capital",
    "ops.working_capital.ccc.days",
    "ops.inventory.turnover",
    "ops.inventory.days",
    "crm.retention.pct",
    "crm.clv.amount",
    "hr.revenue_per_fte.amount",
    "hr.turnover.pct",
    "esg.aligned_revenue.pct",
    "esg.co2.total.tco2e",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  sales.revenue.growth_pct: "Revenue Growth %"
  margin.gm.pct: "Gross Margin %"
  profit.ebitda_margin: "EBITDA Margin %"
  fin.liquidity.working_capital: "Working Capital %"
  ops.working_capital.ccc.days: "Cash Conversion Cycle (Days)"
  ops.inventory.turnover: "Inventory Turnover"
  ops.inventory.days: "Inventory Days on Hand (DIO)"
  crm.retention.pct: "Customer Retention %"
  crm.clv.amount: "Customer Lifetime Value (CLV) Amount"
  hr.revenue_per_fte.amount: "Revenue per FTE Amount"
  hr.turnover.pct: "Employee Turnover %"
  esg.aligned_revenue.pct: "ESG-Aligned Revenue %"
  esg.co2.total.tco2e: "Total CO₂ Emissions (tCO2e)"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: ProductID, type: string, role: product_key }
    - name: fact_balance
      grain: org_period_balance
      primary_key: [OrgID, Period, BalanceLine]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: BalanceLine, type: string, role: attribute }
        - { name: Amount, type: decimal, role: amount }
    - name: fact_working_capital
      grain: org_period_wc
      primary_key: [OrgID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: "DSO Days", type: decimal, role: helper }
        - { name: "DPO Days", type: decimal, role: helper }
        - { name: "DIO Days", type: decimal, role: helper }
    - name: fact_hr
      grain: org_period_hr
      primary_key: [OrgID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: "Headcount FTE", type: decimal, role: helper }
        - { name: "Personnel Cost Amount", type: decimal, role: amount }
        - { name: "Leavers Count", type: int, role: helper }
    - name: fact_customer_metrics
      grain: customer_period
      primary_key: [CustomerID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Active Flag", type: bool, role: indicator }
        - { name: "Churn Flag", type: bool, role: indicator }
        - { name: "CLV Amount", type: decimal, role: amount }
    - name: fact_esg
      grain: org_period_esg
      primary_key: [OrgID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: "ESG-Aligned Revenue Amount", type: decimal, role: amount }
        - { name: "Total Revenue Amount", type: decimal, role: amount }
        - { name: "CO2 Emissions tCO2e", type: decimal, role: amount }
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
        - { name: BusinessUnit, type: string }
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Segment, type: string }
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
        from: fact_sales.CustomerID,
        to: dim_customer.CustomerID,
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
        from: fact_balance.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_balance.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_working_capital.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_working_capital.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_hr.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_hr.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_customer_metrics.CustomerID,
        to: dim_customer.CustomerID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_customer_metrics.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_esg.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_esg.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Customer": "dim_customer[CustomerID]"
  "Product": "dim_product[ProductID]"
  "ESG-Aligned Revenue Amount": "fact_esg[ESG-Aligned Revenue Amount]"
  "Total Revenue Amount": "fact_esg[Total Revenue Amount]"
  "CO2 Emissions tCO2e": "fact_esg[CO2 Emissions tCO2e]"
---

# Enterprise Performance Cockpit

## 1. Business Goal
Provide a single, board-ready cockpit that combines growth, profitability, liquidity, efficiency, customer value, people and ESG KPIs into one view, enabling aligned enterprise steering and prioritization of strategic initiatives.

---

## 2. Business Context
Executive steering is often fragmented across multiple dashboards (sales, finance, operations, HR, ESG), each with its own KPI definitions and timeframes.  
This leads to misaligned conversations: sales celebrates revenue growth while finance highlights margin erosion, operations raises capacity concerns, and ESG reports are detached from core performance.  
The Enterprise Performance Cockpit harmonizes the KPI definitions across domains, links them into a single driver tree, and provides one version of the truth for monthly and quarterly reviews.

---

## 3. Key Questions
- How are revenue, margin, and cash developing versus plan and last year at enterprise and business unit level?
- How does working capital and the cash conversion cycle evolve, and welche Beiträge leisten Inventory, Receivables und Payables?
- Wie entwickelt sich die Kundenbasis (Retention, CLV) und welche Segmente liefern den größten Wert?
- Wie effizient nutzen wir unsere Belegschaft (Revenue per FTE, Turnover)? 
- Wie entwickelt sich unser ESG-Profil (ESG-aligned Revenue, CO₂-Emissionen) im Verhältnis zum wirtschaftlichen Wachstum?
- Welche wenigen Treiber erklären den Großteil der Veränderung in Profitabilität und Cash?

---

## 4. Key KPIs
| Dimension | KPI | Definition (High Level) |
|-----------|-----|--------------------------|
| Growth | Revenue Growth % | (Net Sales - Net Sales LY) / Net Sales LY |
| Profitability | Gross Margin %, EBITDA Margin % | GM% = GM / Net Sales; EBITDA Margin = EBITDA / Net Sales |
| Liquidity | Working Capital %, CCC Days | Working Capital / Net Sales; CCC = DSO + DIO - DPO |
| Efficiency | Inventory Turnover, Inventory Days | Turnover = COGS / Avg Inventory; DIO = 365 / Turnover |
| Customer | Customer Retention %, CLV Amount | Retained Customers / Base; discounted margin per customer |
| People | Revenue per FTE, Turnover % | Net Sales / FTE; Leavers / Avg Headcount |
| ESG | ESG-Aligned Revenue %, Total CO₂ | ESG-eligible revenue share; total emissions in tCO2e |

---

## 5. Required Attributes (Business-Level)
- Time: Year, Quarter, Month
- Org: Region, Business Unit
- Customer: Segment (e.g., Enterprise / SME / Consumer)
- Product: Category, Subcategory
- Financial Structure: P&L and Balance Sheet lines (Net Sales, COGS, Receivables, Inventory, Payables)
- HR: FTE, Personnel Cost, Leavers
- ESG: Revenue classification (ESG-aligned vs non-aligned), Emissions by scope/source

---

## 6. Segmentation & Hierarchies
- Time: Year > Quarter > Month
- Org: Region > Business Unit
- Customer: Segment > Key Account
- Product: Category > Subcategory
- Financial: P&L Structure (Revenue, COGS, Opex, EBITDA) and Balance Sheet Structure (AR, Inventory, AP)

---

## 7. Scope & Assumptions
- Die Cockpit-Sicht nutzt konsolidierte Enterprise-Daten; lokale Abweichungen werden in Detail-Use-Cases analysiert.
- KPI-Definitionen sind an den strategischen KPI-Katalog gekoppelt; Anpassungen erfolgen zentral, nicht auf Cockpit-Ebene.
- Working-Capital- und ESG-Kennzahlen werden mindestens monatlich aktualisiert und mit dem Finance Closing abgestimmt.
- HR- und Customer-Kennzahlen werden auf gleichen Periodenschnitten (Monat/Quartal) wie die Finanzkennzahlen berichtet.
- Das Cockpit dient nicht als operative Detailanalyse, sondern als Startpunkt, von dem aus in tiefergehende Use Cases abgesprungen wird.

---

## 8. Data Freshness & Cadence
- Haupt-Steuerungsrhythmus: monatlich, ergänzt um Quartals- und Jahresansichten.
- Finanz- und Working-Capital-Daten: synchron zum Financial Close (z.B. +3–5 Arbeitstage).
- HR- und ESG-Daten: mindestens monatlich, bei ESG ggf. mit quartalsweiser Detaillierung.
- Customer- und Sales-Daten: täglich/wöchentlich geladen, aber im Cockpit auf Monats-/Quartalsebene verdichtet.

---

## 9. Edge Cases & QA Rules
- Abgrenzung zwischen Management-Reporting und Legal Reporting muss dokumentiert sein (z.B. IFRS vs Management View).
- KPI-Definitionen dürfen sich nicht zwischen Cockpit und Detail-Use-Cases unterscheiden (zentrale Katalogquelle).
- Bei Organisationsänderungen (M&A, Reorganisation) müssen historische Zahlen nachgezogen oder klar gekennzeichnet werden.
- ESG-Datenquellen (z.B. Emissionsfaktoren) müssen versioniert und für Board-Reporting auditierbar sein.
- HR- und Customer-Daten müssen anonymisiert oder aggregiert werden, wo Datenschutz es erfordert.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Konsolidierte Net Sales und Gross Margin nach Org/Time.
  - Working-Capital-Kennzahlen oder Basiskomponenten (AR, Inventory, AP) nach Org/Time.
  - HR-Kennzahlen (FTE, Turnover) nach Org/Time.
  - Kundenbasis (Retention, CLV oder Proxy-Kennzahl) nach Segment.
  - ESG-Aligned Revenue und CO₂-Emissionen nach Org/Time.
- Optional:
  - EBITDA und Net Income nach Org/Time.
  - Detaillierte Produkt- und Kundensegmente für Drilldowns.

---

## 11. Typical Actions
| Dimension | Example Action | Code | Expected Effect |
|-----------|----------------|------|-----------------|
| Growth & Margin | Rebalance Portfolio in schwachen BUs | SP1 | Stabilere GM %, verbesserte Revenue Quality |
| Liquidity | Working Capital Programme starten (DSO/DIO/DPO) | W1 | Kürzerer CCC, mehr freier Cashflow |
| Customer | Fokus auf Retention/CLV-starke Segmente erhöhen | SP2 | Höherer Anteil wertvoller Kunden, stabilere Revenue Base |
| People | Headcount- und Skill-Mix an strategische Prioritäten ausrichten | G1 | Höhere Revenue per FTE, geringerer Turnover in kritischen Rollen |
| ESG | Anteil ESG-aligned Revenue erhöhen | SP2 | Besseres ESG-Profil bei gleichzeitigem Wachstumsfokus |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Alignment | One version of the truth für Vorstand und Bereiche | Anzahl eskalierter KPI-Diskussionen ↓ |
| Profitability | Besser priorisierte Initiativen mit klarer Ergebniswirkung | GM %, EBITDA Margin vs Plan/LY |
| Liquidity | Verbesserter CCC durch konzertierte Maßnahmen | CCC Days, Working Capital % |
| Customer & People | Fokus auf wertschaffende Segmente und Schlüsselrollen | CLV, Retention %, Revenue per FTE |
| ESG | Integration von ESG in die Performance-Diskussion | ESG-Aligned Revenue %, CO₂/Revenue |

---

## 13. Related Processes
Strategic Planning & Budgeting -> Monthly Performance Review -> Steering Committees (Commercial, OPS, HR, ESG) -> Initiative Tracking & Benefit Realization.

---

## 14. Insights & Learnings
Typische Erkenntnisse umfassen Diskrepanzen zwischen Umsatz- und Cash-Wachstum, profitarmen Wachstumsfeldern, unausgewogenen Investitionen in Kunden- oder ESG-Programme sowie Kapazitäts- und People-Engpässe, die in den Einzel-Dashboards nicht sichtbar waren.

---

## 15. Cross-References
- Related Use Cases:  
  `[COR-004 Strategic KPI Dashboard](../COR-004_Strategic_KPI_Dashboard/FactSheet.md)`  
  `[COR-005 Profitability Overview](../COR-005_Profitability_Overview/FactSheet.md)`  
  `[COM-001 Sales Performance vs Plan & LY](../../01_Commercial/COM-001_Sales_Performance/FactSheet.md)`  
  `[OPS-001 Cash Conversion Cycle](../../02_Operational_Efficiency/OPS-001_Cash_Conversion_Cycle/FactSheet.md)`  
  `[CST-001 Customer Retention & Churn](../../03_Customer_and_Market/CST-001_Customer_Retention_and_Churn/FactSheet.md)`  
  `[COR-002 Workforce Productivity & Turnover](../COR-002_Workforce_Productivity_and_Turnover/FactSheet.md)`  
  `[ESG-001 Emission Tracking and Reporting](../../05_ESG/ESG-001_Emission_Tracking_and_Reporting/FactSheet.md)`
- Related Documents:  
  [`Strategic KPIs`](../../../_includes/Strategic_KPIs.md) | [`Use Case Inventory`](../../../_includes/UseCase_Inventory.md) | [`KPI Catalog`](../../../_includes/kpi_catalog/README.md)

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [CEO / CFO / COO] |
| Technical Reviewer | [Lead Enterprise Architect / BI Lead] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first steering cycle] |

---

_Last updated: 19.11.2025_

