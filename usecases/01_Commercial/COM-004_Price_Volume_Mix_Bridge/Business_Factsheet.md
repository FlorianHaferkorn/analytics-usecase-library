---
id: "COM-004"
title: "Price-Volume-Mix Bridge (Î” Net Sales & Î” Gross Margin)"
domain: "Commercial"
owner: "Head of Sales Controlling"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "margin.gm.pct"]
action_codes: ["P2", "M3", "D1", "SP1", "O2"]
expected_impact: "100% reconciled variance; +0.5-1.5 pp GM %; +1-2 pp Î”% Net Sales"

dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: ["Product.Category>Subcategory>SKU","Org.Region>Area>Store","Channel","Time.Year>Month>Week"]
filters_default: ["Time: Last 12M","Org: All","Channel: All"]
qa_asserts: ["RI_OK"]

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
        - { name: Channel, type: string, role: channel }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_product
      grain: product
      primary_key: [ProductID]
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }

model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
required_kpi_ids: [
  "sales.net_sales.delta_amount.ly",
  "margin.gm.delta_amount",
  "sales.pvm.price_effect.amount",
  "sales.pvm.volume_effect.amount",
  "sales.pvm.mix_effect.amount",
  "margin.gm.pct"
]
required_kpis:
  sales.net_sales.delta_amount.ly: "Î” Net Sales Amount"
  margin.gm.delta_amount: "Î” Gross Margin Amount"
  sales.pvm.price_effect.amount: "Price Effect Amount"
  sales.pvm.volume_effect.amount: "Volume Effect Amount"
  sales.pvm.mix_effect.amount: "Mix Effect Amount"
  margin.gm.pct: "Gross Margin %"
---

# Price-Volume-Mix Bridge (Delta Net Sales & Delta Gross Margin) - Business Factsheet

## 1. Summary
- **Business Goal:** Provide a unified analytical bridge that decomposes revenue and margin variance into price, volume, and mix components to explain why results deviate from Plan or Last Year - enabling targeted commercial and cost actions.
- **Target Audience:** Head of Sales Controlling
- **Business Priority:** High
- **Expected Impact:** 100% reconciled variance; +0.5-1.5 pp GM %; +1-2 pp Delta% Net Sales

## 2. Core Questions
- How much of Delta Net Sales and Delta Gross Margin comes from volume, price, or mix?
- Which categories or regions drive mix gains or losses?
- Are positive volume effects offset by unfavorable price or mix?
- How do promotional periods distort PVM relationships?
- What levers can improve the next planning cycle?

## 3. KPI Set (Business View)
| KPI                   | Definition                                         | Unit | Format     |
|-----------------------|----------------------------------------------------|------|------------|
| Delta Net Sales Amount    | Net Sales - Plan/LY                                | EUR  |  #,0.00   |
| Delta Gross Margin Amount | (NS-COGS)_Actual - (NS-COGS)_Plan                  | EUR  |  #,0.00   |
| Price Effect Amount   | (Actual Price - Plan Price)  Actual Qty          | EUR  |  #,0.00   |
| Volume Effect Amount  | (Actual Qty - Plan Qty)  Plan Price              | EUR  |  #,0.00   |
| Mix Effect Amount     | Delta Total - (Price + Volume) Effect                 | EUR  |  #,0.00   |

## 4. Business Logic & Thresholds
- Negative or zero volumes are flagged and excluded from effect calculation where appropriate.
- Extreme price outliers (e.g., below defined floor price) are flagged for review.
- Price + Volume + Mix should reconcile to Total Delta within a small tolerance (e.g., < 0.5 %).
- Referential integrity between fact_sales and dimensions must be  99.5 %.

## 5. Action Codes (Business Perspective)
| Action                                                     | Code | Expected Effect                  |
|------------------------------------------------------------|------|----------------------------------|
| Review price realization by segment and adjust corridors   | P2   | GM % +0.5-1.0 pp                 |
| Refocus promotions to offset unfavorable mix               | D1   | Delta% Net Sales +1-2 pp             |
| Optimize assortment focusing on high-margin products       | M3   | GM % +0.5-1.0 pp, stable revenue |
| Use variance insights to refine next planning assumptions  | SP1  | Lower budget variance, faster cycle |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Delta Net Sales Amount, Delta Gross Margin Amount, Price Effect Amount, Volume Effect Amount, Mix Effect Amount with Plan/LY deltas.
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
- PVM bridge reconciles 100 % of Net Sales and Gross Margin variance between Actual and Plan/LY.
- Effects are calculated on a consistent base (e.g., Plan, Last Year) with clearly documented logic.
- FX effects are either neutralized (constant currency) or explicitly modeled as a separate effect.
- Promotions and one-offs are flagged to avoid misinterpretation of structural price/mix effects.

## 8. Success Criteria
| Dimension      | Expected Impact                      | Measurement  |
|----------------|--------------------------------------|--------------|
| Profitability  | +0.5-1.5 pp GM %                     | vs LY        |
| Transparency   | 100 % reconciled Net Sales & GM Delta    | bridge vs P&L |
| Planning       | -10-20 % manual effort in variance analysis | vs prior year |