---
id: "COM-005"
title: "Promotion ROI & Effectiveness"
domain: "Commercial"
owner: "Head of Marketing Controlling / Trade Marketing"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "margin.gm.pct"]
action_codes: ["D1", "D2", "P2", "M3"]
expected_impact: "+1-2 pp Gross Margin %, +3 % Net Sales in promoted lines"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Channel",
  "Time.Year>Month>Week"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "Baseline_Method_Documented", "Promo_Period_Flag_Consistent"]
required_kpi_ids: [
  "sales.promo.roi.pct",
  "sales.promo.uplift_pct",
  "sales.promo.incremental.amount",
  "margin.promo.incremental.amount",
  "margin.promo.gm.pct",
  "sales.promo.cost.amount"
]
required_kpis:
  sales.promo.roi.pct: "Promo ROI %"
  sales.promo.uplift_pct: "Promo Uplift %"
  sales.promo.incremental.amount: "Incremental Sales Amount"
  margin.promo.incremental.amount: "Incremental GM Amount"
  margin.promo.gm.pct: "GM % During Promo"
  sales.promo.cost.amount: "Promo Cost Amount"
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
        - { name: "Promo Flag", type: bool, role: indicator }
        - { name: "Promo ID", type: string, role: attribute }
        - { name: "Promo Type", type: string, role: attribute }
        - { name: "Promo Cost Amount", type: decimal, role: amount }
    - name: fact_marketing_spend
      grain: promo_campaign
      primary_key: [PromoID]
      required_columns:
        - { name: PromoID, type: string, role: attribute }
        - { name: "Planned Promo Cost Amount", type: decimal, role: amount }
        - { name: "Channel", type: string, role: channel }
        - { name: "Start Date", type: date, role: helper }
        - { name: "End Date", type: date, role: helper }
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
        - { name: Area, type: string }
        - { name: Store, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single, ri_expected: ">=99.5%" }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_marketing_spend.PromoID, to: fact_sales.PromoID, cardinality: one-to-many, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Promo Flag": "fact_sales[Promo Flag]"
  "Promo ID": "fact_sales[Promo ID]"
  "Promo Type": "fact_sales[Promo Type]"
  "Promo Cost Amount": "fact_sales[Promo Cost Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Promotion ROI & Effectiveness

## 1. Business Goal
Quantify the financial return of promotions by measuring incremental revenue and margin uplift versus baseline performance, and enable optimized promotion calendar, depth, and targeting across channels and regions.

---

## 2. Business Context
Promotions are one of the largest controllable investments in commercial planning, yet ROI is oftentimes assessed inconsistently or only at an aggregate level.  
Trade marketing, sales, and finance frequently use different baselines and uplift definitions, which leads to conflicting views on whether promotions are value-accretive or margin-dilutive.  
This use case standardizes how promotional uplift, incremental margin, and ROI are calculated, and links them to a single view of the promotion calendar so that decision makers can reallocate spend towards the most effective campaigns.

---

## 3. Key Questions
- Which promotions deliver the highest incremental sales and gross margin uplift?
- What is the ROI of promotion spend by product, channel, and region?
- How do different promotion mechanics (discount %, bundle, display) perform in terms of ROI versus volume impact?
- How much of promotion volume is truly incremental versus cannibalized from non-promoted products or periods?
- Where can we reduce ineffective promotions or re-invest into higher-ROI campaigns?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Promo ROI % | (Incremental GM Amount - Promo Cost Amount) / Promo Cost Amount | % | 1 decimal |
| Promo Uplift % | (Promo Sales Amount - Baseline Sales Amount) / Baseline Sales Amount | % | 1 decimal |
| Incremental Sales Amount | Promo Sales Amount - Baseline Sales Amount | EUR | 0-2 decimals |
| Incremental GM Amount | (Promo Sales - Promo COGS) - (Baseline Sales - Baseline COGS) | EUR | 0-2 decimals |
| GM % During Promo | (Promo Sales - Promo COGS) / Promo Sales | % | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Date (promotion period start/end)
- Org (region, area, store)
- Product (category, subcategory, SKU)
- Channel (online/offline/wholesale)
- Net Sales Amount, Units Qty
- Promo Flag, Promo ID, Promo Type
- Promo Cost Amount (actual or allocated)
- Optional: List Price Amount, COGS Amount, baselined demand or forecast

---

## 6. Segmentation & Hierarchies
- Product: Category > Subcategory > SKU
- Org: Region > Area > Store
- Channel: Online / Offline / Wholesale
- Promo: Type > Subtype (Price Cut / Bundle / Display)
- Time: Year > Quarter > Month > Week

---

## 7. Scope & Assumptions
- Promo ROI is defined as (Incremental GM Amount - Promo Cost Amount) / Promo Cost Amount.
- Baseline is derived from non-promo periods (e.g., average of last 8–12 weeks) and excludes overlapping campaigns.
- Cannibalization between products or channels is not explicitly modeled in the initial version; future versions may refine uplift attribution.
- Promo Cost Amount can be actuals or allocated from campaign budgets; allocation keys must be documented.
- Reporting currency is EUR; FX conversion at transaction date or monthly average.

---

## 8. Data Freshness & Cadence
- Data refresh: weekly after promo closure (e.g., every Monday 07:00 CET).
- Latency target: <= 3 days after all promo transactions have been posted.
- Historical depth: at least 12–24 months of promotion history for benchmarking.
- Data Owner: Marketing Controlling; Technical Owner: Commercial BI.

---

## 9. Edge Cases & QA Rules
- Promotions with incomplete promo flags or missing cost data are flagged and excluded from ROI ranking.
- Baseline methods must be documented and consistent across products/channels.
- Uplift and ROI are only calculated when baseline and promo periods have sufficient data points.
- Referential integrity between sales and marketing spend tables should be >= 99.5 % on PromoID.
- Double counting across overlapping campaigns must be avoided or explicitly documented.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Sales fact with Net Sales Amount, Units Qty, Date, Org, Product, Channel, Promo Flag/ID/Type.
  - Promo spend or cost fact with PromoID and cost amounts.
- Optional:
  - List Price, COGS, baseline demand, mechanism attributes (leaflet, shelf, display).
- Extended:
  - Customer-level identifiers to assess promo effectiveness by segment or loyalty tier.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Stop or redesign low-ROI promotions | D1 | Promo ROI improves; GM % stabilizes |
| Increase depth or visibility of top-ROI promotions | D2 | Incremental GM and revenue increase |
| Optimize promotion calendar to avoid overlap | P2 | Cannibalization decreases; uplift quality improves |
| Align promo mechanics with price and margin strategy | M3 | Discount leakage reduces; GM % improves |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Profitability | +1–2 pp Gross Margin % in promoted lines | vs Prior Year |
| Revenue | +3 % Net Sales in promoted categories | vs Prior Year |
| Efficiency | -10–20 % ineffective promo spend | vs baseline campaign plan |

---

## 13. Related Processes
Promotion Planning -> Trade Marketing Execution -> In-Store / Digital Activation -> Settlement & Accruals -> Post-Promo Evaluation.

---

## 14. Insights & Learnings
Typical findings include a small share of promotions driving most of the incremental margin, with many low-ROI activities absorbing budget. Linking ROI to mechanics and calendar slots helps codify best practices and reduces wasteful spend.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-001 Sales Performance vs Plan & LY](../COM-001_Sales_Performance/FactSheet.md)`  
  `[COM-003 Promotion Effectiveness (ROI & Uplift)](../COM-003_Promotion_Effectiveness/FactSheet.md)`  
  `[COR-004 Strategic KPI Dashboard](../../04_Corporate_and_Strategy/COR-004_Strategic_KPI_Dashboard/FactSheet.md)`  
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
