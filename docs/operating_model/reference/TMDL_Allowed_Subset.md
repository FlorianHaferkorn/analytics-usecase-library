# TMDL Allowed Subset (Team Standard)
Purpose: Bind our project to a **minimal, consistent subset** of the official TMDL model. This removes ambiguity for authors and MCPs and enables linting/PR checks.

Scope: Applies to all semantic models in this repo (PBIP layout). Desktop is preview/canvas-only; authoring happens in TMDL.

---

## 1) Global Policies
- **Descriptions mandatory** for Tables, Columns, Measures (Copilot-readiness).
- **Star-schema**; conformed dimensions; **clear grain** per fact (invoice line, journal line, snapshot).
- **RLS/OLS only on dimensions**; never on facts.
- **Measures > calculated columns**; role-playing date dimensions allowed.
- **Naming/format (US spelling, EU number format)**:
  - Currency → suffix ` Amount` (format `€ #,0.00`, default summarization **Sum**).
  - Quantity → suffix ` Qty` (integer, **Sum**).
  - Counts → suffix ` Count` / ` Distinct Count` (integer, **Sum** / **DistinctCount**).
  - Percent/rates → suffix ` %` or ` Rate` (format `0.0 %`, default summarization **None**).
  - Time variants → suffixes `YTD`, `MTD`, `QTD`, `YoY`, `MoM`.
- **Technical columns hidden** (`isHidden: true`), default summarization set explicitly.
- DAX does **not** support the assignment operator `:=` (use `=`).

---

## 2) Data Types & Mapping (verbindlich)
Allowed `dataType` values and their defaults (PBIP/TMDL):
| dataType   | Use case                            | Default summarization | Format (if applicable) |
|------------|-------------------------------------|-----------------------|------------------------|
| `int64`    | surrogate keys, counts, qty         | Sum (except keys)     | —                      |
| `double`   | amounts, ratios (when needed)       | Sum (amounts)         | `€ #,0.00` or `0.0 %`  |
| `decimal`  | amounts with fixed precision        | Sum                   | `€ #,0.00`             |
| `string`   | labels, codes                       | None                  | —                      |
| `date`     | calendar date                       | None                  | dd.MM.yyyy             |
| `datetime` | timestamps                           | None                  | dd.MM.yyyy HH:mm       |
| `boolean`  | flags                                | None                  | —                      |

Rules:
- Prefer `decimal` for currency where available; `double` acceptable for engine defaults.
- Use `date` for model time; reserve `datetime` for true timestamps.
- Every measure/column has an explicit `formatString` when currency or percent.

---

## 3) Model (root `model.tmdl`)
**Required**
- `name: string`
- `tables: Table[]`

**Optional (allowed)**
- `relationships: Relationship[]`
- `roles: Role[]`
- `cultures: Culture[]`
- `annotations: Annotation[]`

Constraint:
- One model per domain folder; keep relationships at model root.

---

## 4) Table (`/tables/<name>.tmdl`)
**Required**
- `name: string`
- `columns: Column[]`

**Optional (allowed)**
- `description: string` (**mandatory by policy**)
- `isHidden: boolean`
- `partitions: Partition[]` (see Â§7)
- `measures: []` (prefer separate files under `/measures/...`)

Policies:
- Dimension keys are numeric (`int64`) surrogate keys; business keys may be stored as `string`.
- Technical keys (`*Key`, `*_id`) are `isHidden: true`.
- Table description must include: Purpose Â· Grain & Scope Â· Lineage Â· QA note.

Example (excerpt):
```json
{
  "name": "dim_product",
  "description": "Purpose: master data for product analysis. Grain: product.",
  "columns": [
    { "name": "ProductKey", "dataType": "int64", "isHidden": true, "description": "Surrogate key" },
    { "name": "Product Code", "dataType": "string", "description": "Business code" },
    { "name": "Product Name", "dataType": "string", "description": "Label; Sort by: SortOrder" },
    { "name": "SortOrder", "dataType": "int64", "isHidden": true, "description": "Sort key for Product Name" }
  ]
}
```

---

## 5) Column (inside `columns[]`)
**Required**
- `name: string`
- `dataType: enum { int64, double, decimal, string, date, datetime, boolean }`

**Optional (allowed)**
- `sourceColumn: string`
- `formatString: string`
- `dataCategory: string`
- `sortByColumn: string`
- `isHidden: boolean`
- `description: string` (**mandatory by policy**)

Policies:
- Label columns must define `sortByColumn` if natural sort is not lexical (e.g., month names).
- Geo and currency columns must set `dataCategory` appropriately (see Â§9).
- Default summarization set consistently (keys = None, labels = None).

---

## 6) Measure (separate file `/measures/<folder>/<name>.tmdl`)
**Required**
- `name: string`
- `expression: string` (DAX)

**Optional (allowed)**
- `formatString: string`
- `displayFolder: string`
- `isHidden: boolean`
- `description: string` (**mandatory by policy**)

Policies:
- Provide `displayFolder` and `formatString` for every measure.
- Base measures first; derived measures (`Δ`, `%`) build on base measures.
- No calculated tables for KPI engines; prefer measures.
- Example:
```json
{
  "name": "Gross Margin %",
  "expression": "VAR _ns = [Net Sales Amount] RETURN IF ( _ns = 0, BLANK(), DIVIDE([Gross Margin Amount], _ns) )",
  "formatString": "0.0 %",
  "displayFolder": "02_Margin",
  "description": "Purpose: gross margin share of Net Sales. Definition: [Gross Margin Amount]/[Net Sales Amount]. Grain: aggregated from invoice_line (Date, Org, Product). Unit: %. Lineage: fact_sales. QA: within [-100%;100%]."
}
```

---

## 7) Partitions & Storage Mode
Allowed modes: `import`, `DirectLake`, `DirectQuery`.

Policies:
- Prefer `import` or `DirectLake` for performance and simplicity.
- `DirectQuery` only when latency constraints or data residency demand it.
- Name partitions predictably (e.g., `p_all`, `p_YYYYMM`).

Example (partition excerpt):
```json
{
  "partitions": [
    { "name": "p_all", "mode": "import" }
  ]
}
```

---

## 8) Relationships (model root)
**Required**
- `fromTable`, `fromColumn`, `toTable`, `toColumn`
- `crossFilteringBehavior: "single" | "both"`

Policies:
- Cardinality: Many-to-One from fact→dimension.
- Default filtering: **single** direction (dim→fact). `both` only by exception and documented.
- Inactive relationships allowed only with rationale; role-playing dates encouraged.

Example:
```json
{
  "fromTable": "fact_sales",
  "fromColumn": "DateKey",
  "toTable": "dim_date",
  "toColumn": "DateKey",
  "crossFilteringBehavior": "single"
}
```

---

## 9) DataCategory (whitelist & duties)
Whitelist (examples): `Currency`, `Country`, `StateOrProvince`, `City`, `Address`, `PostalCode`, `WebURL`, `ImageURL`, `Barcode`.

Duties:
- Currency codes/labels set `dataCategory: "Currency"`.
- Geo fields set appropriate category to enable maps (used only when there is real geo value).
- URLs must use `WebURL` / `ImageURL` categories for safe rendering.

---

## 10) Display Folders (taxonomy)
Every measure must have a folder. Recommended taxonomy per domain:
- `01_Sales`, `02_Margin`, `03_Customer`, `10_Time Intelligence`, `90_Admin`, `99_QA`

Columns typically **no** folders; hide technical columns.

---

## 11) Format Strings & Locale
- Currency: `€ #,0.00` (EU punctuation; use project theme locale for visuals).
- Percent: `0.0 %` (always explicit).
- Integers: `#,0` (no decimals).
- Dates: `dd.MM.yyyy` as display (storage remains date/datetime).

---

## 12) Sort-By-Column Policy (examples)
- Month label (`MMM` or localized name) → `sortByColumn: MonthNumber`.
- Product name → `sortByColumn: SortOrder` when required.
- Any non-lexical label must declare its sorter column (hidden).

---

## 13) Descriptions — Required Template
For every Table/Column/Measure, descriptions must follow this mini-template (one paragraph):
- **Purpose:** one sentence business purpose.
- **Definition:** formula/logic; numerator/denominator; filters.
- **Grain & Scope:** aggregation grain; scope (Actual/Plan, etc.).
- **Unit/Format:** currency/unit/%.
- **Lineage:** source tables/fields.
- **QA:** check/range/tolerance.

Example (measure description inside JSON as string):
```
"description": "Purpose: share of gross margin relative to Net Sales. Definition: ([Net Sales Amount]-[COGS Amount])/[Net Sales Amount]. Grain: aggregated from invoice line. Unit: %. Lineage: fact_sales. QA: within [-100%;100%]."
```

---

## 14) Roles / RLS (minimal standard)
- Define roles only on dimension tables (e.g., Org/Region).
- Keep expressions deterministic and documented in model README if complex.
- Naming: `RLS_<Domain>_<Scope>` (e.g., `RLS_Sales_Region`).

---

## 15) Cultures / Translations (optional)
- Add cultures when localized labels or format strings are required.
- Maintain translation keys aligned with display names; avoid partial translations.

---

## 16) Annotations & Naming Conventions (optional)
- Reserve prefix `_` for internal annotations.
- Avoid spaces in file names; spaces allowed in `name` but keep them consistent with display folders.

---

## 17) QA Measures (required for critical KPIs)
- Add hidden assert measures in folder `99_QA` (e.g., value ranges, reconciliation checks).
- Example: `%` measures must be within `[-100%; 100%]`; revenue reconciles to GL within tolerance.

---

## 18) Illustrative Snippets

### Table (dim_date excerpt)
```json
{
  "name": "dim_date",
  "description": "Purpose: canonical date dimension. Grain: one row per calendar date.",
  "columns": [
    { "name": "DateKey", "dataType": "int64", "isHidden": true, "description": "Surrogate key" },
    { "name": "Date", "dataType": "date", "description": "Calendar date" },
    { "name": "Month Name", "dataType": "string", "description": "Display label; Sort by: Month No" },
    { "name": "Month No", "dataType": "int64", "isHidden": true, "description": "Sort key for Month Name" }
  ]
}
```

### Measure (Net Sales Amount)
```json
{
  "name": "Net Sales Amount",
  "expression": "SUM ( fact_sales[Net Sales Amount] )",
  "formatString": "€ #,0.00",
  "displayFolder": "01_Sales",
  "description": "Purpose: net sales in reporting currency. Definition: sum of fact_sales[Net Sales Amount]; excludes returns if already net. Grain: invoice line aggregated. Unit: currency. Lineage: fact_sales. QA: reconciles to P&L within ±0.1%."
}
```

---

## 19) Compliance Checklist (for PRs/Lint)
- Descriptions present for all objects.
- Measures have `displayFolder` and correct `formatString` (currency/%).
- Technical columns hidden; label columns sorted.
- Relationships single-direction; cardinality Many-to-One; rationale for exceptions.
- Storage mode per policy; partitions properly named.
- QA measures exist for critical KPIs.

---

**End of Allowed Subset**


