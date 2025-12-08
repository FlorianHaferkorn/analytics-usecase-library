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
  sales.net_sales.delta_amount.ly: "Î” Net Sales Amount vs LY"
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

# Integrated Margin Bridge (P&L Driver Tree) - Business Factsheet

## 1. Summary
- **Business Goal:** Provide a fully reconciled P&L driver tree that explains changes from Net Sales to Gross Margin and EBITDA by price, volume, mix, COGS and other drivers, enabling management to focus on the most impactful levers.

---
- **Target Audience:** CFO / Head of Controlling
- **Business Priority:** Very High
- **Expected Impact:** Provide a board-ready, fully reconciled driver tree from Net Sales to Gross Margin, EBITDA and Net Result across price, mix, volume, COGS, logistics, supplier terms and FX.

## 2. Core Questions
- Wie viel des Margen- und Ergebnis-Changes ist auf Preis-, Volumen- und Mixeffekte zurckzufhren?
- Welchen Beitrag leisten COGS, Logistikkosten, Rabatte und FX zur Vernderung von GM % und EBITDA?
- Wie verteilen sich die Treiber auf Regionen, Business Units und Produktkategorien?
- Welche Treiber sind dauerhaft (strukturell) und welche nur temporr (z.B. Einmalaufwendungen)?
---

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| n/a | n/a | n/a | n/a |

## 4. Business Logic & Thresholds
- n/a

## 5. Action Codes (Business Perspective)
TODO: add action table.

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Net Sales Amount, Gross Margin Amount, Gross Margin %, EBITDA Margin %, ÃŽâ€ Net Sales Amount vs LY with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Initiative drill-down.
- Drill-through to financial plan vs actual detail.
- Export-ready table including action status.

## 7. Dependencies & Constraints
- n/a

## 8. Success Criteria
- n/a