---
id: "COM-003"
title: "Promotion Effectiveness (ROI & Uplift)"
domain: "Commercial"
owner: "Head of Marketing Controlling"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi:
  - "Gross Margin %"
  - "Revenue Growth %"
supports_strategic_kpi_ids:
  - "margin.gm.pct"
  - "sales.revenue.growth_pct"
action_codes:
  - "D1"
  - "P2"
  - "D2"
  - "O2"
  - "SP1"
expected_impact: "+10-30 % ROI uplift; +0.5-1.0 pp GM %; +1-3 pp Delta% Net Sales"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  - "Product.Category>Subcategory>SKU"
  - "Org.Region>Area>Store"
  - "Channel"
  - "Time.Year>Month>Week"
filters_default:
  - "Time: Last 12M"
  - "Org: All"
  - "Channel: All"
qa_asserts:
  - "RI_OK"
  - "Promo_Baseline_Validated"
required_kpi_ids:
  - "sales.promo.roi.pct"
  - "sales.promo.uplift_pct"
  - "sales.promo.incremental.amount"
  - "margin.promo.incremental.amount"
  - "margin.promo.gm.pct"
  - "sales.promo.cost.amount"
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
        - { name: PromoID, type: string, role: promo_key }
        - { name: PromoFlag, type: boolean, role: attribute }
    - name: fact_promo_events
      grain: promo_product_day
      primary_key: [PromoID, ProductID, Date]
      required_columns:
        - { name: PromoID, type: string, role: promo_key }
        - { name: Promo Type, type: string, role: attribute }
        - { name: Promo Cost Amount, type: decimal, role: amount }
        - { name: Discount %, type: decimal, role: attribute }
        - { name: Start Date, type: date, role: start_date }
        - { name: End Date, type: date, role: end_date }
    - name: fact_promo_baseline
      grain: promo_product_day
      primary_key: [PromoID, ProductID, Date]
      required_columns:
        - { name: Baseline Sales Amount, type: decimal, role: amount }
        - { name: Baseline Units Qty, type: decimal, role: quantity }
        - { name: Baseline GM Amount, type: decimal, role: amount }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
        - { name: Week, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_product
      grain: product
      primary_key: [ProductID]
    - name: dim_channel
      grain: channel
      primary_key: [Channel]
    - name: dim_promo
      grain: promo
      primary_key: [PromoID]
      required_columns:
        - { name: Promo Name, type: string }
        - { name: Promo Mechanic, type: string }
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single, ri_expected: ">=99.9%" }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.Channel, to: dim_channel.Channel, cardinality: many-to-one, direction: single }
    - { from: fact_sales.PromoID, to: dim_promo.PromoID, cardinality: many-to-one, direction: single }
    - { from: fact_promo_events.PromoID, to: dim_promo.PromoID, cardinality: many-to-one, direction: single }
    - { from: fact_promo_events.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_promo_baseline.PromoID, to: dim_promo.PromoID, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Promo Cost Amount": "fact_promo_events[Promo Cost Amount]"
  "Baseline Sales Amount": "fact_promo_baseline[Baseline Sales Amount]"
  "Baseline GM Amount": "fact_promo_baseline[Baseline GM Amount]"
  "Promo Type": "dim_promo[Promo Mechanic]"
  "Date": "dim_date[Date]"
  "Channel": "dim_channel[Channel]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Promotion Effectiveness (ROI & Uplift) – Business Factsheet

## 1. Summary
- **Business Goal:** Quantify the financial return of promotions by measuring incremental revenue and margin uplift versus baseline performance, and translate the findings into optimized calendar planning, depth, and audience targeting.
- **Target Audience:** Head of Marketing Controlling
- **Business Priority:** High
- **Expected Impact:** +10‑30 % ROI uplift; +0.5‑1.0 pp GM %; +1‑3 pp Delta% Net Sales

## 2. Core Questions
- Which promotions generated the highest incremental sales and margin uplift?
- What is the ROI of promotion spend by product, channel, and region?
- How do different promo mechanics (discount %, bundle, display) perform?
- What share of promotion volume was incremental versus cannibalized?
- Which calendar periods or customer segments deliver the best return on promo spend?

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Promo ROI % | (Incremental GM − Promo Cost) / Promo Cost | % | 1 decimal |
| Promo Uplift % | (Promo Sales − Baseline Sales) / Baseline Sales | % | 1 decimal |
| Incremental Sales Amount | Promo Sales − Baseline Sales | EUR | 0‑2 decimals |
| Incremental GM Amount | (Promo GM − Baseline GM) | EUR | 0‑2 decimals |
| GM % During Promo | (Promo NS − Promo COGS) / Promo NS | % | 1 decimal |
| Promo Cost Amount | All trade investments linked to PromoID | EUR | 0‑2 decimals |

## 4. Business Logic & Thresholds
- Only promotions ≥ 2 days and ≥ 5 transactions included; short events treated as noise.
- ROI is capped between −100 % and +500 % to prevent outlier bias; values outside range flagged for review.
- Baseline sales derived from the rolling average of comparable non-promo weeks (−8 to −2 weeks before event); overlapping promos are excluded from the baseline window.
- Incremental uplift must reconcile with total market/segment growth (tolerance ±5 %).
- Referential integrity required ≥ 99.9 % for Date, Org, Product, Channel, PromoID.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Optimize promotion calendar by ROI ranking | D1 | Delta% GM +0.5‑1.0 pp; ROI +10‑20 % |
| Reduce depth or duration of low-return discounts | P2 | GM % +0.5 pp; NS stable |
| Focus investment on high-return mechanics / bundles | D2 | ROI +15‑30 % |
| Improve baseline forecasting & promo tagging accuracy | O2 | Forecast bias −10 %; reporting stability improves |
| Link trade marketing bonuses to measured ROI | SP1 | Structural improvement in ROI discipline |

## 6. 3‑30‑300 Page Layout
### 6.1 3‑Second Layer (Insight)
- KPI cards for Promo ROI %, Promo Uplift %, Incremental Sales Amount, Incremental GM Amount, Promo Cost Amount with deltas vs Plan and LY.
- Threshold-based callouts (e.g., ROI < 0 % or uplift < +2 %) and quick summary of top/bottom promos.

### 6.2 30‑Second Layer (Story)
- Trend chart (12‑24 months) for ROI %, GM %, and incremental sales to spot seasonality.
- Variance waterfall decomposing ROI change into price, volume, mix, and cost drivers.
- Ranking visuals: top/bottom promos by ROI, channel heatmap for uplift vs spend, scatter of discount depth vs ROI.

### 6.3 300‑Second Layer (Detail)
- Matrix with Org × Product × Promo Type, including ROI, uplift, and GM %.
- Drill-through to promo event details (PromoID, mechanic, spend, incremental units).
- Export table summarizing planned vs actual KPIs, action owner, and follow-up status.

## 7. Dependencies & Constraints
- Requires aligned data from sales, trade marketing spend, and promo master data (PromoID as single key).
- Baseline computation depends on stable weekly sales history; new SKUs or limited editions require manual override.
- Need standardized promo tagging across channels; eCommerce flash sales must map to same PromoID for comparability.
- Currency EUR; FX conversions applied at transaction date; for multi-country view use constant currency restatement.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| ROI Improvement | +10‑30 % ROI uplift | vs previous quarter |
| Profitability | +0.5‑1.0 pp GM % | vs LY |
| Forecast Stability | −10 % forecast bias | Rolling 3M horizon |
| Promo Discipline | ≥ 80 % of promo spend tied to measurable ROI | Coverage ratio |

