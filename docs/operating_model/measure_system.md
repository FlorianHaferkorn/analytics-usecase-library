# Measure System

Purpose:
- Define a consistent, governed system for all measures in the ActionReady Analytics Framework.

Scope:
- Measure taxonomy and naming conventions
- KPI ID scheme vs. measure names
- Formatting standards (currency, %, counts, deltas)
- DisplayFolder conventions
- Supporting vs. KPI measures
- Documentation standard (Copilot-ready)
- Validation and quality checks

Position in the framework:
- WHY (company layer) sets strategic KPIs and questions.
- HOW (operating model) implements logic via semantic layer + measure system.
- WITH WHAT/PATTERNS (framework) catalogs and templates reference measures.
- WHAT (usecases) consume governed measures by `kpi_id`.

Measure taxonomy:
- Amount (currency), Qty, Count/Distinct Count, %, Rate, Variance/Variance %, Time Intelligence.
- One primary type per measure; qualifiers (YoY, MTD, etc.) via naming suffixes.

KPI IDs vs. Measure Names:
- `kpi_id`: stable ASCII ID in KPI Catalog (`<domain>.<topic>.<measure>.(amount|pct|count|days|...)`).
- Measure names: user-facing with symbols (Δ for variances, % suffix); currency handled via `formatString`, not in names.

Formatting standards:
- Currency: `"€ #,0.00"` (or `"€ #,0"` for large aggregates)
- Percent: `"0.0 %"` (or `"0.00 %"` when needed)
- Counts/Qty: `#,0`; durations with decimals only if needed.

DisplayFolders (examples):
- Commercial: `01_Sales`, `02_Margin`, `03_Price_Promo`, `03_Customer`
- Operations: `01_Capacity`, `02_Inventory`, `03_SupplyChain`
- Corporate/Governance: `01_Strategy`, `01_Workforce`, `01_DataQuality`, `01_Compliance`, `01_RiskControl`, `01_Audit`
- ESG: `01_ESG`, `01_Energy`
- Technical/supporting measures may use a technical folder (e.g. `10_Tech`) and be hidden.

KPI vs. Supporting Measures:
- KPI measures map 1:1 to `kpi_id`, exposed to users, fully documented.
- Supporting measures implement reusable logic; hidden where possible.
- KPI measures orchestrate supporting measures, not deep nested logic reused elsewhere.

Documentation (Copilot-ready):
- Purpose, Definition (logic, numerator/denominator), Grain & Scope, Unit/Format, Lineage, QA.
- Supporting measures at least: Purpose, Definition, Lineage.

Authoring & Governance Flow:
1) Use case lists `required_kpi_ids`.
2) KPI Catalog holds canonical definition for each `kpi_id`.
3) Semantic model exposes exactly one KPI measure per `kpi_id`; formatting/foldering from catalog.
4) Validation ensures IDs exist, measures match catalog, naming/formatting/folders comply, descriptions exist.

Quality & Performance:
- Reuse supporting measures; avoid repeated heavy logic.
- Prefer measures over calculated columns; keep star-schema-friendly.
- Run lint/BPA checks (see `_internal/tools/linters`) before release.

Cleaning & Best Practices:
- No TBD in catalogs/models; use conservative definitions if unsure.
- Strict consistency: every `required_kpi_id` must exist in catalog and in the semantic model.
- No uncontrolled cross-use-case measures; shared logic lives in catalogs + domain dictionaries.
