---
id: "INN-001"
title: "Innovation Pipeline Performance"
domain: "Innovation & People"
owner: "Head of Strategy & Innovation"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Innovation Rate %", "New Product Revenue %"]
supports_strategic_kpi_ids: ["people.new_product_share"]
action_codes: ["I2"]
expected_impact: "+1 pp Innovation Rate durch besseres Pipeline-Management und Priorisierung."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Portfolio.Pillar>Program>Project",
  "Product.Category>Subcategory>SKU",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 24M",
  "Status: All"
]
qa_asserts: ["RI_OK", "Idea_Stages_Consistent"]
required_kpi_ids: [
  "people.new_product_share"
]
required_kpis:
  people.new_product_share: "New Product Share %"
data_requirements:
  facts:
    - name: fact_innovation
      grain: idea
      primary_key: [IdeaID]
      required_columns:
        - { name: IdeaID, type: string, role: attribute }
        - { name: Stage, type: string, role: attribute }
        - { name: CreatedDate, type: date, role: date_key }
        - { name: ImplementedFlag, type: bool, role: indicator }
    - name: fact_sales
      grain: product_month
      primary_key: [ProductID, Month]
      required_columns:
        - { name: ProductID, type: string, role: product_key }
        - { name: Month, type: date, role: date_key }
        - { name: NetSalesAmount, type: decimal, role: amount }
        - { name: IsNewProduct, type: bool, role: indicator }
  dims:
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
model_mapping:
  "Idea ID": "fact_innovation[IdeaID]"
  "Idea Stage": "fact_innovation[Stage]"
  "Product ID": "fact_sales[ProductID]"
  "Net Sales Amount": "fact_sales[NetSalesAmount]"
---

# INN-001 Innovation Pipeline Performance - Business Factsheet

## 1. Summary
- **Business Goal:** Increase the hit rate of innovation investments by balancing the idea funnel, accelerating stage progression, and maximizing revenue from new launches.
- **Target Audience:** Chief Innovation Officer, Strategy leads, Portfolio managers, Product management.
- **Business Priority:** High due to dependency on innovation for growth.
- **Expected Impact:** +1 pp innovation rate and faster conversion from idea to launch via data-driven prioritization.

## 2. Core Questions
- How many ideas sit in each pipeline stage and is the portfolio balanced (discover, define, develop, deploy)?
- What is the conversion rate from idea to commercialization, and where do bottlenecks occur?
- How much revenue do products launched in the last 24 months contribute vs targets?
- Which categories, regions, or programs deliver the most value and which need intervention?

## 3. KPI Set (Business View)
| KPI Name | Purpose | Business Definition | Interpretation | Decision Relevance |
|----------|---------|---------------------|----------------|--------------------|
| Idea-to-Launch Conversion % | Measures funnel effectiveness. | Percentage of ideas that progress from intake to implemented within a defined timeframe. | Rising trend indicates healthy prioritization; low values highlight stage bottlenecks. | Triggers portfolio balancing and resource reallocation. |
| Pipeline Velocity (Days) | Indicates speed of progression. | Average days between stage entry and next gate for active ideas. | > Target (e.g., 120 days) indicates process friction. | Guides process simplification and governance focus. |
| New Product Revenue Share % | Quantifies impact post-launch. | Net revenue from products launched within last 24 months divided by total revenue. | Target depends on industry (e.g., >15 %). | Validates ROI of innovation investments and informs budget cycles. |
| Innovation Throughput | Shows overall capacity. | Count of ideas exiting each stage per quarter. | Decline signals resource constraints or governance delays. | Used to plan staffing and funding waves. |

## 4. Business Logic & Thresholds
- Pipeline velocity measured per stage (idea -> concept, concept -> pilot, pilot -> launch) with executive thresholds defined per portfolio.
- Conversion % computed on rolling 12-month cohort of ideas to avoid stale backlog bias.
- New product revenue qualifies for 24 months after launch date, then flows into base revenue.
- Programs missing metadata (stage, owner, value) flagged for data remediation before governance reviews.

## 5. Action Codes (Business Perspective)
| Code | Name | Business Description | Typical Trigger | Expected Effect |
|------|------|-----------------------|-----------------|------------------|
| I2 | Portfolio Fast-Track | Reassign resources, remove blockers, or accelerate governance for high-value ideas. | Conversion % < target or critical initiative delayed. | +10-20 % throughput increase in affected stages; faster launch. |

## 6. 3-30-300 Page Layout
### 6.1 3-Second Layer (Insight)
- KPI cards for Idea-to-Launch Conversion %, Pipeline Velocity, New Product Revenue Share %, Pipeline Inventory.
- Alert for stages breaching SLA or high-value idea stuck > threshold.

### 6.2 30-Second Layer (Story)
- Funnel visual Stage distribution by count/value.
- Timeline of stage exits vs plan, highlighting fast-track items.
- Revenue contribution chart for new launches by category/region.

### 6.3 300-Second Layer (Detail)
- Kanban-style table listing ideas with stage, value, owner, blockers, and action code status.
- Drillable matrix Portfolio Pillar > Program > Project with KPIs and milestone progress.
- Export-ready backlog for governance committees.

## 7. Dependencies & Constraints
- Innovation management tool must capture stage, owner, business case, and decision dates; no free-text-only records.
- Product master must flag new products with launch date to attribute revenue correctly.
- Financial attribution of new product revenue needs consistent mapping between innovation IDs and product IDs.
- Governance cadence (monthly) relies on timely data updates (max 2-day lag).

## 8. Success Criteria
- Leading: 95 % of stage gate decisions recorded within 5 days; dashboard adopted by portfolio PMO weekly.
- Lagging: +1 pp innovation rate, conversion % meets target, and new product revenue share stays within strategic range.