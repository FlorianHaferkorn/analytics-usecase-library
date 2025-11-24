# INN-001 Innovation Pipeline Performance - Technical Factsheet

## 1. Data Contract (YAML)
Define tables, grain, keys, types.

`yaml
dimension:
  - name: dim_portfolio
    grain: portfolio_item
    columns:
      - {name: IdeaID, type: text, role: primary_key}
      - {name: PortfolioPillar, type: text}
      - {name: Program, type: text}
      - {name: ProjectName, type: text}
      - {name: Owner, type: text}
      - {name: StageOrder, type: int}
  - name: dim_product
    grain: product
    columns:
      - {name: ProductID, type: text, role: primary_key}
      - {name: Category, type: text}
      - {name: Subcategory, type: text}
      - {name: LaunchDate, type: date}
  - name: dim_date
    grain: date
    columns:
      - {name: Date, type: date, role: primary_key}
fact:
  - name: fact_innovation
    grain: idea_stage_event
    primary_key:
      - IdeaID
      - Stage
      - StageEntryDate
    columns:
      - {name: IdeaID, type: text, role: portfolio_key, ref: dim_portfolio}
      - {name: Stage, type: text, role: attribute}
      - {name: StageEntryDate, type: date_key, ref: dim_date}
      - {name: StageExitDate, type: date, role: helper}
      - {name: ExpectedValueEUR, type: decimal, role: amount}
      - {name: Probability, type: decimal, role: attribute}
      - {name: ImplementedFlag, type: boolean, role: indicator}
  - name: fact_sales
    grain: product_month
    primary_key:
      - ProductID
      - Month
    columns:
      - {name: ProductID, type: text, role: product_key, ref: dim_product}
      - {name: Month, type: date_key, ref: dim_date}
      - {name: NetSalesAmount, type: decimal, role: amount}
      - {name: IsNewProduct, type: boolean, role: indicator}
relationships:
  - from: fact_innovation.IdeaID
    to: dim_portfolio.IdeaID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_innovation.StageEntryDate
    to: dim_date.Date
    cardinality: many-to-one
    cross_filter: single
  - from: fact_sales.ProductID
    to: dim_product.ProductID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_sales.Month
    to: dim_date.Date
    cardinality: many-to-one
    cross_filter: single
settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
`

## 2. Semantic Model Requirements
- Facts sourced from innovation management tool and sales mart; combined in a single dataset to enable KPI tracing from idea to revenue.
- Stage values standardized (Discover, Define, Develop, Deploy, Launch) with numeric StageOrder for sorting.
- Need mapping table between IdeaID and ProductID for revenue attribution; stored as part of dim_portfolio or separate bridge table ridge_idea_product (not shown) referencing product launches.
- Relationship directions remain single; use calculation groups for stage-based time intelligence if needed.
- Hidden helper columns: StageExitDate, probability, gating notes for drill-through only.
- Hierarchies: Portfolio Pillar > Program > Project; Product Category > Subcategory > SKU; Date Year > Quarter > Month.

## 3. Measures (DAX + Description)
`
Ideas Count =
    // TODO: Provide DAX via Power BI MCP counting distinct dim_portfolio[IdeaID]
`
Description:
  Purpose: Base metric for pipeline inventory.
  Definition: Distinct count of ideas filtered by stage/time.
  Unit/Format: Whole number.
  Lineage: dim_portfolio[IdeaID].
  QA: Must match innovation tool export.

`
Idea-to-Launch Conversion % =
    // TODO: Provide DAX via Power BI MCP dividing Ideas implemented by total ideas in cohort
`
Description:
  Purpose: Measures funnel effectiveness.
  Definition: Implemented ideas / total ideas for selected cohort using DIVIDE.
  Unit/Format: Percentage 1 decimal.
  Lineage: fact_innovation[ImplementedFlag], dim_portfolio.
  QA: Compare vs PMO report.

`
Pipeline Velocity (Days) =
    // TODO: Provide DAX via Power BI MCP calculating average DATEDIFF(StageEntryDate, StageExitDate, DAY)
`
Description:
  Purpose: Shows stage throughput.
  Definition: Average days between entry and exit for current filter context.
  Unit/Format: Decimal days.
  Lineage: fact_innovation dates.
  QA: Validate vs stage gate logs.

`
New Product Revenue Amount =
    // TODO: Provide DAX via Power BI MCP summing NetSalesAmount where IsNewProduct = TRUE()
`
Description:
  Purpose: Revenue attributable to launches.
  Definition: Sum of NetSalesAmount for IsNewProduct true and within 24 months of launch.
  Unit/Format: Currency 0.
  Lineage: fact_sales.
  QA: Tie out vs finance innovation report.

`
New Product Revenue Share % =
    // TODO: Provide DAX via Power BI MCP dividing [New Product Revenue Amount] by [Net Sales Amount]
`
Description:
  Purpose: KPI for innovation impact.
  Definition: Ratio of new product revenue to total revenue.
  Unit/Format: Percentage 1 decimal.
  Lineage: fact_sales.
  QA: Variance <= 0.5 pp vs finance deck.

## 4. Defaults & Formatting
| Field | Setting | Notes |
|-------|---------|-------|
| Ideas Count | Sum, Whole number | Display folder: 01_Pipeline |
| Idea-to-Launch Conversion % | No summarization, Percentage 1 | Display folder: 01_Pipeline |
| Pipeline Velocity (Days) | No summarization, Decimal 1 | Display folder: 01_Pipeline |
| New Product Revenue Amount | Sum, Currency 0 | Display folder: 02_NewProducts |
| New Product Revenue Share % | No summarization, Percentage 1 | Display folder: 02_NewProducts |
| Stage | Ordered categorical | Sort by StageOrder |

## 5. Visual Requirements (Technical)
| Visual | Purpose | Required Fields | Notes |
|--------|---------|-----------------|-------|
| Funnel | Show stage inventory | Stage, Ideas Count, Expected Value | Use StageOrder for sorting |
| KPI Cards | Headline metrics | Conversion %, Velocity, New Product Revenue Share %, Pipeline Inventory | Include data fields for variance vs plan |
| Timeline | Stage exits over time | Date hierarchy, Ideas Count by Stage Exit | Show annotations for fast-track initiatives |
| Revenue Composition | Post-launch impact | Category/Subcategory, New Product Revenue Amount | 24M rolling window |
| Detail Table | Governance view | Idea ID, Stage, Owner, Expected Value, Action Code | Add drill-through to project brief |

## 6. Performance & Refresh
- Storage mode: Import; incremental refresh on StageEntryDate (rolling 36M) and sales Month (rolling 36M) to limit dataset size.
- Partition facts by month; ensure innovation API ingestion supports query folding via parameterized date filters.
- Refresh cadence: innovation data nightly; revenue data daily post-close; additional refresh before portfolio board.
- Monitor bridging table for IdeaID->ProductID as mapping grows.

## 7. RLS/OLS Requirements
- Role Innovation_Global: full access for Strategy & Innovation.
- Role Portfolio_Manager: filter dim_portfolio[Owner] or Program according to mapping table.
- Role Category_Manager: restrict dim_product[Category] for product-level revenue views.
- Sensitive financial expectations (ExpectedValueEUR) optionally hidden for non-executive roles.

## 8. QA & Validation Rules
| Check Type | Object | Rule | Tolerance |
|------------|--------|------|-----------|
| Referential Integrity | fact_innovation -> dim_portfolio | 100 % IdeaID match | Hard fail |
| Referential Integrity | fact_sales -> dim_product | >= 99.9 % ProductID match | 0.1 % |
| Idea_Stages_Consistent | fact_innovation | Each idea must have monotonic StageOrder progression | Hard fail |
| New Product Mapping | bridge Idea -> Product | Each implemented idea mapped to at least one product | 0 missing |
| Revenue Share Tie-Out | New Product Revenue Share % | Compare vs finance validation file | +/- 0.5 pp |
