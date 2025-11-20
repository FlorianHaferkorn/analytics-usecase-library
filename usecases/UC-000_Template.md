---
id: "{{PREFIX}}-000"
title: "[Insert Use Case Title]"
domain: "[Commercial / Operational Efficiency / Customer & Market / Corporate & Strategy]"
owner: "[Business Owner / Responsible Department]"
impact: "[High / Medium / Low]"
status: "[Draft / Ready / Archived]"
last_update: "DD.MM.YYYY"
reporting_level: "[Strategic / Tactical / Operational]"
analytics_stage: "[Descriptive / Diagnostic / Predictive / Prescriptive]"
maturity: "[Idea / Pilot / Production]"
supports_strategic_kpi: ["Readable KPI Name"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct"]
action_codes: ["P2","D1"]
expected_impact: "[Narrative of expected outcome, e.g., '+2-5 pp ?% Net Sales']"
dataset_model: "[PBIP model name, e.g., Contoso Sales Sample for Power BI Desktop.SemanticModel]"
page_template: "[overview_drivers_details | drivers_details | other registered template]"
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
qa_asserts: ["RI_OK","DeltaPct_PositivePlan"]
required_kpi_ids: [
  "sales.net_sales.amount",
  "sales.net_sales.delta_pct.ly"
]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  sales.net_sales.delta_pct.ly: "?% Net Sales"
data_requirements:
  facts:
    - name: fact_main
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
    - { from: fact_main.Date, to: dim_date.Date, cardinality: many-to-one, direction: single, ri_expected: ">=99.9%" }
    - { from: fact_main.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_main.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_main[Net Sales Amount]"
  "Units Qty": "fact_main[Units Qty]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Use Case Fact Sheet
Short, descriptive title summarizing the analytical question (e.g., "Sales Performance vs Plan & Last Year"). Copy this template into your Use Case folder as `FactSheet.md` and replace every placeholder.

Authoring help (business): `../docs/Business_Playbook.md`  
Schema reference: `./SCHEMA.md`

---

## 1. Business Goal
Explain in one to two sentences why this analysis is important for business steering or decision-making. Focus on the business outcome, not the technical metric.

---

## 2. Business Context
Provide concise background information describing:
- The underlying business challenge or opportunity.
- The key decisions supported by this analysis.
- Dependencies such as planning cycles, data cadence, or linked processes.

---

## 3. Key Questions
List the guiding analytical questions this use case addresses:
- What happened?
- Where did it happen?
- Why did it happen?
- What should we do next?

---

## 4. Key KPIs
Each KPI must exist in the shared KPI Catalog (`/_includes/kpi_catalog/README.md`).

| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| [KPI Name] | [Brief definition or formula] | [€, %, pcs, days] | [Format, e.g., 0-2 decimals] |
| [? KPI Name] | [Variance vs Plan or LY] | [€, %, pcs, days] | [? or ?% notation] |

> Naming rules: `?` = absolute variance, `?%` = relative variance, `%` suffix for percentages, `Amount` = currency, `Qty` = quantity, `Count` = integer.

---

## 5. Required Attributes (Business-Level)
List the minimum fields required for this use case (business language).

- Date (transaction date)
- Org (store/region)
- Product (name/category)
- Channel (sales channel or customer type)
- Net Sales Amount, Units Qty
- Optional: Promotion Flag/Type, List Price Amount

---

## 6. Segmentation & Hierarchies
Define the main dimensions and hierarchies used for analysis.

- Org: Region > Area > Store
- Product: Category > Subcategory > SKU
- Channel: Online / Offline / Partner
- Time: Year > Month > Day

---

## 7. Scope & Assumptions
Document key assumptions and analytical boundaries.

- Sales = invoice-line granularity, returns excluded from Net Sales
- Reporting currency = EUR; FX rate at transaction date
- Plan version = current board-approved plan
- Actuals = validated monthly close data
- Time zone = Europe/Berlin

---

## 8. Data Freshness & Cadence
Define expected refresh behavior and latency.

- Data source refresh: daily at 06:00 CET
- Latency <= 24h
- Historical backfill = 90 days
- Ownership: [System / Team responsible]

---

## 9. Edge Cases & QA Rules
List known exceptions and quality gates before publishing.

- No negative Net Sales Amount (except return flows)
- Percentages bounded (e.g., Price Realization % in [0%; 150%])
- Referential integrity >= 99.9 % across Date/Org/Product
- All Plan versions validated and frozen before publication
- Missing dimension members default to "Unknown"

---

## 10. Minimum Viable Dataset (MVD)
Define the minimum data fields required to launch a basic version of this use case.

- Date, Org, Product, Net Sales Amount, Units Qty
- Optional: Plan Amount, Last Year Amount
- Extend with Promo Type, List Price, Margin data for advanced version

---

## 11. Typical Actions
List 3-5 operational levers or actions derived from this analysis. Reference standardized Action Codes (`/_includes/ActionCodes.md`).

| Action | Code | Expected Effect |
|---------|------|-----------------|
| [Describe action briefly] | [P2 / D1 / W1 ...] | [e.g., GM% +1-2 pp, DSO -5 days] |

---

## 12. Expected Business Impact
Quantify or qualify the expected business improvement.

| Dimension | Expected Impact | Measurement |
|------------|-----------------|------------|
| Revenue | +2-5 pp ?% Net Sales | vs Plan |
| Profitability | +0.5-1 pp Gross Margin % | vs LY |
| Liquidity | DSO -5 days | vs Prior Quarter |

---

## 13. Related Processes
List linked processes or organizational areas.

---

## 14. Insights & Learnings
Summarize recurring insights or findings observed during the analysis.

---

## 15. Cross-References
Provide links to related use cases or documentation.

- **Related Use Cases:**  
  `[{{PREFIX}}-002 Related Use Case](../<ClusterFolder>/{{PREFIX}}-002_Example/FactSheet.md)`  

- **Related Documents:**  
  [`Reporting Strategy`](../docs/Reporting_Strategy.md)  
  [`Methodology`](../docs/Methodology.md)  
  [`KPI Catalog`](../_includes/kpi_catalog/README.md)  
  [`Action Codes`](../_includes/ActionCodes.md)  
  [`Glossary`](../_includes/Glossary.md)

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Name / Role] |
| Technical Reviewer | [Name / Role] |
| Version | v1.0 |
| Review Date | DD.MM.YYYY |
| Review Notes | [Summary of review or comments] |

---

<!--
USAGE NOTES
- Store the fact sheet as `FactSheet.md` inside `usecases/{cluster}/{ID}_{Slug}/` (e.g., `usecases/01_Commercial/COM-001_Sales_Performance/FactSheet.md`).
- Always update `required_kpis` when adjusting `required_kpi_ids`; validators expect a 1:1 match.
- Replace {PREFIX} with your 3-letter cluster code (e.g., COM, OPS, CST, COR).
- Run `./tools/coverage/validate_factsheets.ps1` after every edit to ensure schema compliance.
- The Front-Matter doubles as machine-readable spec for coverage checks and measure generation.
-->
