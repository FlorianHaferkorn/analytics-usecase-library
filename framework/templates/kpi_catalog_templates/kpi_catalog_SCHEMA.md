# KPI & Measure Schema

Purpose: Single source of truth for the structure of

1) KPI Catalog entries (business-level KPIs)
2) Domain Measure Dictionary entries (technical measures in semantic models).

The KPI Catalog is BUSINESS truth (what we steer on).  
The Measure Dictionary is TECHNICAL truth (how we calculate it).

---

## 1. KPI Catalog Schema

Each KPI is a YAML object inside a list (typically in `KPI_Catalog_*.md`
inside ```yaml code fences).

### 1.1 Fields (KPI)

Top-level:

- `kpi_id` (required, string)  
  Stable machine ID in format `domain.metric.id` (lowercase, dot-separated).  
  Must be unique across all KPI catalogs.
- `kpi_key` (required, string)  
  Human-readable KPI name used in reports.
- `kpi_type` (required, enum)  
  Type of KPI (metric nature): `amount`, `count`, `quantity`, `percentage`, `rate`, `index`, `variance_amount`, `variance_percentage`, `activity`, `diagnostic`, `status`.
- `kpi_role` (optional, enum)  
  Role of KPI: `strategic` or `supporting`.  
  kpi_role SHOULD be added to KPI entries once layout checks allow it.
- `impact_dimension` (required, enum)  
  Impact dimension this KPI belongs to, e.g. `Growth`, `Profitability`.
- `domain_tag` (required, list<string>)  
  1..n domain tags, e.g. `["Commercial"]`, `["SupplyChain","Retail"]`.
- `use_case_ref` (required, list<string>)  
  IDs of use cases where this KPI is central, e.g. `["COM-001","COM-004"]`.  
  Use an explicit empty list if none apply.
- `action_code_ref` (required, list<string>)  
  IDs of Action Codes that reference this KPI, e.g. `["C-M2.1","C-P4.1"]`.  
  Use an explicit empty list if none apply.
- `calc_type` (required, enum)  
  Calculation type: `amount`, `rate`, `ratio`, `count`.

Section `business` (required):
- `business.purpose` (required, string)  
  One-sentence business purpose of the KPI.
- `business.definition` (required, string)  
  Business definition / calculation logic in words (no DAX).
- `business.grain_scope` (required, string)  
  Aggregation grain and scope, e.g. `Invoice line aggregated by Month, Org, Product`.
- `business.unit_format` (required, string)  
  Unit and format, e.g. `€ (0–2 decimals)`, `% (1 decimal)`, `pcs`.
- `business.interpretation` (required, string)  
  How to interpret the KPI (good/bad range, typical values, caveats).

Section `technical` (required):
- `technical.dax_name` (required, string)  
  Semantic measure name in the implementation tool.  
  Field name remains for compatibility; actual measure names vary by tool.
- `technical.depends_on_measures` (required, list<string>)  
  Measure names this KPI depends on, e.g. `["Net Sales Amount","COGS Amount"]`.  
  **No DAX expression here.**
- `technical.lineage` (required, list<string>)  
  Source tables/columns, e.g. `fact_sales.Net Sales Amount`.
Section `governance` (required):
- `governance.business_owner` (required, string)  
  Business owner role/person.
- `governance.data_owner` (required, string)  
  Data owner responsible for data quality.
- `governance.steward` (optional, string)  
  Operational owner / data steward.
- `governance.review_cycle` (required, string)  
  Review cycle, e.g. `monthly`, `quarterly`.
- `governance.validation_process` (required, string)  
  Short description of how the KPI is validated/reconciled.
- `governance.qa_rules` (required, list<string>)  
  Concrete QA rules (bounds, reconciliation rules, outlier checks).
- `governance.version` (required, string)  
  Semantic version of the KPI entry, e.g. `v1.0`.

Section `metadata_quality` (required):
- `metadata_quality.completeness_score` (required, float 0..1)  
  Heuristic completeness indicator based on filled required fields.
- `metadata_quality.last_review` (required, string, date)  
  Date of last review in format `DD.MM.YYYY`.
Optional:
- `aliases` (optional, list<string>)  
  Alternative names / synonyms.

### 1.2 Allowed values (KPI)

- `kpi_type`: `amount`, `count`, `quantity`, `percentage`, `rate`, `index`, `variance_amount`, `variance_percentage`, `activity`, `diagnostic`, `status`
- `kpi_role`: `strategic`, `supporting`
- `impact_dimension`:
  - `Growth`
  - `Profitability`
  - `Liquidity`
  - `Efficiency`
  - `Customer`
  - `ESG`
  - `Governance`
  - `Risk`
  - `InnovationPeople`
- `calc_type`: `amount`, `rate`, `ratio`, `count`

### 1.3 KPI Example

```yaml
- kpi_id: "margin.gross_margin_pct"
  kpi_key: "Gross Margin %"
  kpi_type: "percentage"
  kpi_role: "strategic"
  impact_dimension: "Profitability"
  domain_tag:
    - "Commercial"
  use_case_ref:
    - "COM-001"
    - "COM-004"
  action_code_ref:
    - "C-M2.1"
    - "C-P4.1"
  calc_type: "ratio"
  business:
    purpose: "Measures profitability relative to net sales."
    definition: "(Net Sales Amount − COGS Amount) / Net Sales Amount."
    grain_scope: "Invoice line aggregated by Date, Org, Product, Channel."
    unit_format: "% (1 decimal)"
    interpretation: "Higher is better; negative values indicate loss-making segments."
  technical:
    dax_name: "Gross Margin %"
    depends_on_measures:
      - "Net Sales Amount"
      - "COGS Amount"
    lineage:
      - "fact_sales.Net Sales Amount"
      - "fact_sales.COGS Amount"
  governance:
    business_owner: "Head of Controlling"
    data_owner: "Finance BI"
    steward: "Senior Controller"
    review_cycle: "monthly"
    validation_process: "Reconcile with P&L gross margin during month-end close."
    qa_rules:
      - "Value must be between -100 % and 100 %."
      - "Reconcile with official P&L within ±0.5 pp at company level."
    version: "v1.0"
  metadata_quality:
    completeness_score: 0.95
    last_review: "21.11.2025"
```

### What does NOT belong in the KPI Catalog

- Tool-specific logic or expressions (DAX/SQL/etc.)
- Helper or performance-only measures
- Technical optimization notes
- Report/UI-specific calculations

### Validation Rules (declarative)

- Every `kpi_id` is unique across all KPI catalogs.
- `kpi_role` SHOULD be added to KPI entries once layout checks allow it.
- Supporting KPIs must not be Action Code triggers.
- `use_case_ref` is required (list; empty list allowed).
- `action_code_ref` is required (list; empty list allowed).
- All referenced KPI IDs must exist.
- No tool-specific syntax in KPI Catalog entries.
