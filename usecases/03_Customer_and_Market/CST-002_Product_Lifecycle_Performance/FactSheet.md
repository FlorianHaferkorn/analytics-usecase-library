---
id: "CST-002"
title: "Product Lifecycle Performance"
domain: "Customer and Market"
owner: "Head of Category Management / Product Strategy"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Innovation Revenue %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "margin.gm.pct", "prod.lifecycle.new_share.pct"]
action_codes: ["D1", "SP1", "P2", "SP2", "M3"]
expected_impact: "-10-20 % SKU count; +2 pp GM %; +3-5 % revenue from new launches"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Lifecycle.Stage",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Lifecycle Stage: All"
]
qa_asserts: ["RI_OK", "LaunchDate_Present", "Phase_Coverage_Complete"]
required_kpi_ids: [
  "prod.lifecycle.new_share.pct",
  "prod.contribution_margin.pct",
  "prod.lifecycle.age.months",
  "prod.roi.pct",
  "prod.lifecycle.phase_distribution.pct"
]
required_kpis:
  prod.lifecycle.new_share.pct: "New Product Share %"
  prod.contribution_margin.pct: "Product Contribution Margin %"
  prod.lifecycle.age.months: "Lifecycle Age (months)"
  prod.roi.pct: "Product ROI %"
  prod.lifecycle.phase_distribution.pct: "Phase Distribution %"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "COGS Amount", type: decimal, role: amount }
        - { name: "Promo Cost Amount", type: decimal, role: amount }
        - { name: Channel, type: string, role: channel }
    - name: fact_product_investment
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: LaunchDate, type: date, role: date_key }
        - { name: DevelopmentCost, type: decimal, role: amount }
        - { name: MarketingCost, type: decimal, role: amount }
        - { name: LifecycleStage, type: string, role: attribute }
  dims:
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
        - { name: Brand, type: string }
        - { name: Status, type: string }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_product_investment.ProductID, to: dim_product.ProductID, cardinality: one-to-one, direction: both }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "COGS Amount": "fact_sales[COGS Amount]"
  "Promo Cost Amount": "fact_sales[Promo Cost Amount]"
  "Development Cost": "fact_product_investment[DevelopmentCost]"
  "Marketing Cost": "fact_product_investment[MarketingCost]"
  "Launch Date": "fact_product_investment[LaunchDate]"
  "Lifecycle Stage": "fact_product_investment[LifecycleStage]"
  "Product": "dim_product[ProductID]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
---

# Product Lifecycle Performance

## 1. Business Goal
Maximize category profitability and portfolio efficiency by tracking the performance of products throughout their lifecycle - from launch to maturity and phase-out - and by steering innovation, pricing, and discontinuation decisions based on data.

---

## 2. Business Context
Assortments bloat when launches are not phased out quickly enough and mature SKUs keep cannibalizing shelf space. Category managers need a holistic view of how each product contributes to growth, margin, and ROI at every stage. Finance demands proof that innovation spend converts into incremental revenue, while Operations needs clarity on when to stop replenishing tail products. This use case stitches together sales, cost, marketing, and lifecycle metadata to enable objective, cross-functional lifecycle steering.

---

## 3. Key Questions
- How do products perform across lifecycle stages (Launch, Growth, Maturity, Decline)?
- Which SKUs deliver the highest contribution and ROI?
- When should a product be discontinued or relaunched?
- How do pricing, margin, and promotion intensity evolve per phase?
- What share of sales comes from new vs. existing products?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| New Product Share % | Revenue from products launched <12m / Total revenue | % | 1 decimal |
| Product Contribution Margin % | (NS - COGS - Promo Cost) / Net Sales | % | 1 decimal |
| Lifecycle Age (months) | Months since Launch Date | months | 0 decimals |
| Product ROI % | (GM - DevCost - MktCost) / (DevCost + MktCost) | % | 1 decimal |
| Phase Distribution % | Revenue share per lifecycle stage | % | stacked |

---

## 5. Required Attributes (Business-Level)
- Product ID, Category, Subcategory, Launch Date
- Net Sales Amount, COGS Amount, Promo Cost Amount
- Units Qty, Margin Amount, Marketing Cost, Development Cost
- Optional: Product Status (Active, Phase-Out), Country, Channel

---

## 6. Segmentation & Hierarchies
- Product: Category > Subcategory > SKU > Variant
- Lifecycle: Launch / Growth / Maturity / Decline / Phase-Out
- Org: Region > Area > Store
- Channel: Retail / eCom / Wholesale
- Time: Year > Quarter > Month

---

## 7. Scope & Assumptions
- Lifecycle classification based on sales age and trend: Launch (<6m), Growth (6-18m), Maturity (18-36m), Decline (>36m or Δ% NS < -20 % YoY).
- Product ROI = (GM - DevCost - MktCost) / (DevCost + MktCost).
- Currency = EUR; FX at transaction date.
- Products inactive for >12 months automatically 'Phase-Out'.
- Innovation share defined as revenue from SKUs launched within last 24 months.

---

## 8. Data Freshness & Cadence
- Sales and cost data refresh daily.
- Lifecycle classification re-run weekly after master updates.
- Marketing/innovation cost actuals loaded monthly after close.
- Data Owner: Category Analytics; Technical Owner: Commercial BI.

---

## 9. Edge Cases & QA Rules
- Product Launch Date must exist for lifecycle assignment.
- Phase classification must cover 100 % of portfolio.
- Missing cost components default to zero (flagged 'Incomplete').
- Referential integrity >= 99.9 % across Date/Product/Org.
- Phase transitions validated quarterly.

---

## 10. Minimum Viable Dataset (MVD)
- Required: Sales + COGS by Product/Date, Launch Date per SKU.
- Optional: Promo cost, development/marketing investments, lifecycle flags.
- Extended: Distribution coverage, competitor benchmark, customer adoption metrics.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Accelerate ramp-up of new launches via targeted promotions | D1 | Δ% NS +5-10 pp (Launch) |
| Reduce tail portfolio complexity (phase-out) | SP1 | COGS reduces; GM % improves |
| Adjust pricing of mature SKUs to protect margin | P2 | GM % +0.5-1 pp |
| Reinvest in top-growth categories and winning SKUs | SP2 | Δ% NS +2-4 pp |
| Optimize marketing mix across lifecycle stages | M3 | ROI +10-15 % |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Portfolio Efficiency | SKU count -10-20 % | vs baseline |
| Profitability | +2 pp GM % | vs Plan |
| Innovation | +3-5 % revenue from launches | vs Prior Year |

---

## 13. Related Processes
Portfolio Management -> Product Development -> Category Planning -> Pricing & Promotion Strategy.

---

## 14. Insights & Learnings
Tail SKUs consume 40 % of operational effort while contributing <10 % of gross margin. Launches that fail to reach 1 % share within six months rarely recover without a major repositioning.

---

## 15. Cross-References
- Related Use Cases:  
  `[CST-001 Customer Retention & Churn](../CST-001_Customer_Retention_and_Churn/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
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
