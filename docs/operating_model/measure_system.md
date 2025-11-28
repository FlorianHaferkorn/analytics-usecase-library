# Measure System

Status: Draft (Internal)

## Purpose
Define a consistent, governed system for all measures in the **ActionReady Analytics Framework**.  
The measure system ensures that KPIs and supporting measures are:
- semantically consistent across domains,
- technically robust and performant,
- Copilot-/AI-ready through complete metadata,
- and tightly aligned with data contracts, semantic models, and use cases.

---

## Scope

Included:
- Measure taxonomy and naming conventions
- KPI ID scheme vs. measure names
- Formatting standards (currency, %, counts, deltas)
- DisplayFolder conventions
- Use of supporting measures vs. KPI measures
- Documentation standard (Copilot template)
- Validation and quality checks

Not included:
- Tool-specific DAX/M code samples
- Domain-specific measure definitions (see semantic model dictionaries)
- Individual KPI definitions (see KPI Catalog)

---

## 1. Position in the Framework

The measure system connects:

- **Company Layer (WHY)**  
  Strategic KPIs and key questions determine *what* must be measured.

- **Operating Model (HOW)**  
  Semantic layer and measure system together define *how* logic is implemented.

- **Framework (WITH WHAT)**  
  KPI Catalog, Action Codes, templates and glossaries consume and reference measures.

- **Use Case Library (WHAT)**  
  Each use case specifies `required_kpi_ids` and relies on governed measures.

---

## 2. Measure Taxonomy

All measures must be classified into one of the following categories:

- **Amount**  
  Currency values (0–2 decimals), e.g. `Net Sales Amount`.

- **Qty**  
  Quantities as integers, e.g. `Units Sold Qty`.

- **Count / Distinct Count**  
  Entity counts, e.g. `Customer Count`, `Customer Distinct Count`.

- **% (Percent)**  
  Ratios and shares, typically 1–2 decimals, e.g. `Gross Margin %`.

- **Rate**  
  Rates per time or unit, e.g. `Return Rate`, `Conversion Rate`.

- **Variance / Variance %**  
  Absolute and relative differences vs. target or prior period.

- **Time Intelligence**  
  YTD, MTD, QTD, YoY, MoM, rolling windows (7/30/60 days), etc.

Each measure must have exactly one primary type; additional qualifiers (e.g. YoY, MTD) are expressed via naming suffixes.

---

## 3. KPI IDs vs. Measure Names

### 3.1 KPI IDs

- `kpi_id` is a stable, technical identifier managed in the KPI Catalog.  
- Format: ASCII, dot-separated namespace:

  `<domain>.<topic>.<measure>.(amount|pct|count|days|...)`

- Examples:
  - `sales.net_sales.amount`
  - `margin.gm.pct`
  - `ops.oee.pct`
  - `crm.clv.amount`
  - `people.digital_adoption.pct`

`kpi_id` is never shown to end users; it is used for governance, tooling, and lineage.

### 3.2 Measure Names (User-Facing)

- Measure names are verbal, readable names for end users.
- Symbols are allowed and standardized:
  - Delta: `Δ` in the name (e.g. `Δ Net Sales Amount`, `Δ% Net Sales`).
  - Percent: suffix `%` (e.g. `Gross Margin %`).
- Currency:
  - No hard-coded currency codes in the name (e.g. no `EUR` in the name).
  - Currency representation is handled via `formatString`.

Supporting measures must be clearly named and reusable, e.g.:
- `Net Sales Amount`
- `Net Sales Amount LY`
- `Baseline Sales Amount`
- `Promo Sales Amount`

Complex logic must not be hidden directly inside KPI measures when used in multiple places; instead, use explicit supporting measures.

---

## 4. Formatting Standards

Formatting is part of the measure specification and must be consistent across domains.

### 4.1 Currency

- Standard amounts (two decimals):  
  `formatString: "€ #,0.00"`
- Large aggregated values where decimals are not meaningful:  
  `formatString: "€ #,0"`

### 4.2 Percent

- Standard percent:  
  `formatString: "0.0 %"`  
  (if needed, use `0.00 %` for highly sensitive ratios).

### 4.3 Counts / Qty / Time

- Counts, units, hours (integer):  
  `formatString: "#,0"`
- Hours/Duration with one decimal (if needed):  
  `formatString: "#,0.0"`

All measure dictionaries must include the intended format.

---

## 5. DisplayFolder Conventions

DisplayFolders group measures by business meaning, not by technical implementation.

Examples (to be adapted per domain):

- **Commercial**
  - `01_Sales`
  - `02_Margin`
  - `03_Price_Promo`
  - `03_Customer`

- **Operations**
  - `01_Capacity`
  - `02_Inventory`
  - `03_SupplyChain`

- **Corporate / Governance**
  - `01_Strategy`
  - `01_Workforce`
  - `01_DataQuality`
  - `01_Compliance`
  - `01_RiskControl`
  - `01_Audit`

- **ESG**
  - `01_ESG`
  - `01_Energy`

New measures must reuse and align to these patterns to keep a consistent model navigation experience.

Technical/supporting measures should be placed in clearly labeled technical folders (e.g. `10_Tech`) and typically be hidden from end users.

---

## 6. KPI Measures vs. Supporting Measures

- **KPI Measures**
  - Represent business KPIs with a `kpi_id` in the KPI Catalog.
  - Are the primary measures exposed in reports (Overview, Insights, Explorer).
  - Must be documented using the full Copilot template.

- **Supporting Measures**
  - Implement reusable logic used by multiple KPIs.
  - Stay hidden from users where possible.
  - Examples: base amounts, baselines, prior periods, helper numerators/denominators.

Principle:
- KPI measures should orchestrate logic by combining supporting measures, not contain deeply nested logic themselves when reused in multiple places.

---

## 7. Measure Documentation (Copilot Template)

Every KPI measure must be documented with the following fields:

- **Purpose**: One-sentence purpose.
- **Definition**: Formula/logic; numerator/denominator; filter assumptions.
- **Grain & Scope**: Aggregation grain (e.g. invoice line aggregated by Date, Org, Product) and scope (Actual, Plan, Forecast).
- **Unit/Format**: Currency/unit/%/duration, including expected `formatString`.
- **Lineage**: Source table(s), key fields, and upstream data contracts.
- **QA**: Validation rule, expected range or sanity checks.

Supporting measures should at least have `Purpose`, `Definition`, and `Lineage`.

This documentation is mandatory for AI/Copilot readiness and for governance.

---

## 8. Authoring & Governance Flow (High Level)

1. **Use Case defines `required_kpi_ids`**  
   - In the use case factsheet, each use case lists the KPI IDs it requires.

2. **KPI Catalog holds KPI definitions**  
   - For each `required_kpi_id`, there is a canonical entry in the KPI Catalog with:
     - `kpi_id`
     - `kpi_key`
     - `kpi_type`
     - business & technical definition
     - unit, format, grain, and lineage

3. **Semantic Model exposes measures**  
   - For each `kpi_id`, there is exactly one KPI measure in the semantic model.
   - Measure name is derived from `kpi_key`, formatting and folder from KPI metadata.
   - Supporting measures are added as needed.

4. **Validation & QA**  
   - Automated checks ensure:
     - Every `required_kpi_id` from use cases exists in the KPI Catalog.
     - Every catalog `kpi_id` used in a use case has a measure in the semantic model.
     - Measures follow naming, formatting, and foldering rules.
     - Descriptions are present for all KPI measures.

Tooling (scripts/linters) in `_internal/tools/` can be used to automate these checks.

---

## 9. Cleaning & Best Practices

- **No “TBD” in productive catalogs or use cases**  
  If the business definition is not fully clear, use a conservative but meaningful definition and refine later.

- **Strict consistency between Factsheet, KPI Catalog, and Semantic Model**  
  - Every `required_kpi_id` in a factsheet must:
    - exist as `kpi_id` in the KPI Catalog, and
    - correspond to exactly one KPI measure in the semantic model.

- **No uncontrolled cross-use-case measures**  
  - Shared logic must be modeled in KPI Catalog + domain measure dictionaries, not by copying measures between models.

- **Prefer measures over calculated columns**  
  - Calculated columns are only used when absolutely necessary for model behavior (e.g. SortBy, group keys).

---

## 10. Performance & Quality Considerations

- Avoid repeated heavy calculations in KPI measures; reuse supporting measures.
- Minimize context transitions and unnecessary complex filters.
- Align measure logic with star schema design to keep queries efficient.
- Regularly run semantic/BPA checks to maintain quality over time.

---

**Location to place this file:**  
`docs/operating_model/measure_system.md`
