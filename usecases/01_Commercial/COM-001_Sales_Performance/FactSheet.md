---
id: "COM-001"
title: "Sales Performance vs Plan & Last Year"
domain: "Commercial"
owner: "Head of Sales"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "margin.gm.pct"]
action_codes: ["P2", "D1", "M3", "SP1"]
expected_impact: "+2-5 pp Î”% Net Sales; +0.5-1.5 pp Gross Margin %"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Channel",
  "Time.Year>Month>Week>Day"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "DeltaPct_OnlyWhenPlanPositive"]
required_kpi_ids: [
  "sales.net_sales.amount",
  "sales.net_sales.delta_amount.ly",
  "sales.net_sales.delta_pct.ly",
  "sales.price.realization_pct",
  "sales.promo.uplift_pct",
  "sales.pvm.price_effect.amount",
  "sales.pvm.volume_effect.amount",
  "sales.pvm.mix_effect.amount",
  "margin.gm.pct",
  "margin.gm.amount"
]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  sales.net_sales.delta_amount.ly: "Î” Net Sales Amount"
  sales.net_sales.delta_pct.ly: "Î”% Net Sales"
  sales.price.realization_pct: "Price Realization %"
  sales.promo.uplift_pct: "Promo Uplift %"
  sales.pvm.price_effect.amount: "Price Effect Amount"
  sales.pvm.volume_effect.amount: "Volume Effect Amount"
  sales.pvm.mix_effect.amount: "Mix Effect Amount"
  margin.gm.pct: "Gross Margin %"
  margin.gm.amount: "Gross Margin Amount"
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
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_product
      grain: product
      primary_key: [ProductID]
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single, ri_expected: ">=99.9%" }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Sales Performance vs Plan & Last Year

## 1. Business Goal
Ensure sustainable revenue growth by identifying and explaining deviations from Plan and Last Year early enough to steer pricing, promotions, and channel mix toward margin-accretive growth.

---

## 2. Business Context
Sales is the primary driver of both liquidity and profitability. Variances versus Plan or Last Year often arise from a combination of volume, price, mix, and promotion effects. Without a standardized variance logic, discussions focus on symptoms rather than causes.  
This use case provides a structured revenue bridge (Plan -> Actual) and enables data-driven corrective actions across channels, products, and regions.

---

## 3. Key Questions
- What is the Î” and Î”% of Net Sales vs Plan and Last Year?  
- Which regions, products, or channels drive over-/underperformance?  
- What are the main drivers: price, volume, mix, or promo depth?  
- Which levers can recover revenue shortfalls or protect margins?  
- How quickly can trends be detected and acted upon?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Net Sales Amount | Total invoiced sales excl. returns and taxes | EUR | 0-2 decimals |
| Î” Net Sales Amount | Net Sales - Plan (or LY) | EUR | 0-2 decimals |
| Î”% Net Sales | (Net Sales - Plan) / Plan | % | 1 decimal |
| Price Realization % | Net Price / List Price | % | 1 decimal |
| Promo Uplift % | (Promo Sales - Baseline) / Baseline | % | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Date (transaction date)  
- Org (region, area, store)  
- Product (category, subcategory, SKU)  
- Channel (online/offline/partner)  
- Net Sales Amount, Units Qty  
- Optional: Promotion Flag, List Price Amount, Plan Amount, LY Amount

---

## 6. Segmentation & Hierarchies
- Org: Region > Area > Store  
- Product: Category > Subcategory > SKU  
- Channel: Online / Offline / Partner  
- Time: Year > Month > Week > Day

---

## 7. Scope & Assumptions
- Sales at invoice-line granularity, returns excluded from Net Sales  
- Reporting currency EUR; FX at transaction date  
- Plan version = current board-approved plan  
- Actuals based on validated monthly close data  
- Time zone = Europe/Berlin

---

## 8. Data Freshness & Cadence
- Refresh frequency: daily at 06:00 CET  
- Latency <= 24h  
- Backfill = 90 days  
- Data Owner: Commercial BI Team

---

## 9. Edge Cases & QA Rules
- No negative Net Sales Amount except for return flows  
- Î”% Net Sales computed only when Plan > 0  
- Price Realization % bounded [0%; 150%]  
- Referential integrity >= 99.9 % across Date/Org/Product  
- Missing dimensions default to 'Unknown' category

---

## 10. Minimum Viable Dataset (MVD)
- Required: Date, Org, Product, Net Sales Amount, Units Qty  
- Optional: Plan Amount, LY Amount  
- Extended: List Price, Promo Type, Margin Data  

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Tighten Discounts - enforce corridor and reduce leakage | P2 | GM % +0.5-1.5 pp; NS stable |
| Optimize Promo Calendar - align depth and timing with demand | D1 | Î”% NS +1-3 pp; Forecast accuracy improves |
| Rebalance Channel/Product Mix toward high-margin items | M3 | GM % +1.0 pp; Î”% NS stable |
| Invest/Divest selectively across under/overperforming areas | SP1 | Profitability improves; capital efficiency improves |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| Revenue | +2-5 pp Î”% Net Sales | vs Plan |
| Profitability | +0.5-1.5 pp Gross Margin % | vs LY |
| Forecast Accuracy | +10-20 % lower MAPE | 4-8 week horizon |

---

## 13. Related Processes
Sales Planning and Forecasting -> Pricing Governance -> Promotion Management -> Channel Strategy -> Account Planning.

---

## 14. Insights & Learnings
Price Realization usually contributes more to GM % variance than volume effects outside promotions.  
Promo intensity correlates inversely with overall margin quality â€” balanced governance yields optimal ROI.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-002 Gross Margin Analysis](../COM-002_Gross_Margin_Analysis/FactSheet.md)`  
  `[COM-003 Promotion Effectiveness](../COM-003_Promotion_Effectiveness/FactSheet.md)`  
  `[OPS-001 Cash Conversion Cycle](../../02_Operational_Efficiency/OPS-001_Cash_Conversion_Cycle/FactSheet.md)`
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Name / Role] |
| Technical Reviewer | [Name / Role] |
| Version | v1.0 |
| Review Date | DD.MM.YYYY |
| Review Notes | [Summary of comments] |

---

_Last updated: 04.11.2025_

