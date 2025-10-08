# Includes

This folder contains shared reference files that provide definitions and metadata used across all use cases.

## Structure
| File | Purpose |
|------|----------|
| **Glossary.md** | Defines abbreviations, business terms, and analytical concepts. |
| **KPI_Catalog.md** | Lists all standardized KPIs with definitions, formulas, and QA rules. |
| **ActionCodes.md** | Contains standardized operational levers (P2, D1, etc.) for consistent use across domains. |

## Usage
- Reference these files from any use case with relative Markdown links.  
  Example: `[See KPI Catalog](../_includes/KPI_Catalog.md)`
- Do not duplicate definitions inside individual use cases.
- Update these files through Pull Requests only (review required).

---

## KPI Catalog Schema (Standard)

The `KPI_Catalog.md` file defines all measures using a unified schema.  
Each KPI must contain business, technical, and governance metadata.  
This ensures Copilot-readiness, automated documentation, and model validation.

```yaml
kpi_key: "<canonical name>"            # Unique name (e.g., "Net Sales Amount")
aliases: []                             # Optional synonyms or legacy names

domain_tag: [Commercial]                # 1..n: Commercial, Operational, Customer, Corporate, Strategy, ESG, Procurement, SupplyChain, People, Finance, Marketing, Portfolio
use_case_ref: [COM-001]                 # 1..n Use Case IDs (e.g., COM-001, OPS-001)

calc_type: base                         # base | derived | ratio | variance | variance_pct | composite | index
refresh: daily                          # daily | weekly | monthly | quarterly
status: Active                          # Draft | Active | Deprecated
owner_role: "Sales Controlling"         # Functional owner

business:
  purpose: >                            # Clear business objective
    Measure total invoiced sales excluding returns and taxes to steer revenue growth and detect shortfalls early across org/product/channel.
  definition: >                         # Business logic and filters
    Sum of invoiced sales excluding taxes and returns; cancellations reduce value in the period they are posted.
  grain_scope: >                        # Aggregation grain and scope
    Invoice line; applicable to Actual and Plan at Date–Org–Product–Channel.
  unit_format: "€; 0–2 decimals"        # Unit and format (€, %, pcs, days)
  acceptance_criteria: >                # Optional. Validation thresholds
    Reconciles to GL revenue within ±0.5 % at month-end close.

technical:
  dax_name: "Net Sales Amount"          # Final DAX name
  dax_expression: |                     # DAX formula (or placeholder)
    Net Sales Amount = SUM ( fact_sales[Net Sales Amount] )
  aggregation: sum                      # sum | avg | count | distinctcount | none
  format_string: "€ #,##0.00"           # Numeric format
  display_folder: "Sales"               # Folder in semantic model
  data_category: "Currency"             # Optional
  sort_by: ""                           # Optional
  dependencies: []                      # Upstream measures (if derived)
  lineage:
    tables: [fact_sales]                # Source tables
    columns: ["fact_sales.Net Sales Amount"]  # Source columns
  dims:                                 # Conformed dimensions
    date: "dim_date[Date]"
    org: "dim_org[OrgKey]"
    product: "dim_product[ProductKey]"
    channel: "dim_channel[ChannelKey]"
    customer: "dim_customer[CustomerKey]"

governance:
  qa_rules:                             # At least 2–3 testable rules
    - "Value ≥ 0 at any grain; else flag 'NEGATIVE_NS'."
    - "Reconcile vs GL revenue within ±0.5 % at month close."
    - "Referential integrity ≥ 99.9 % on Date/Org/Product."
  edge_cases: []                        # Optional. Special handling
  rls_ols:                              # Optional. Security settings
    rls_on_dim: ["dim_org", "dim_customer"]
    ols_on_columns: []
  notes: ""                             # Optional. Additional remarks
```

---

### Naming & Formatting Rules

| Type | Rule | Example |
|------|------|----------|
| Variance | Prefix with `Δ` | Δ Net Sales Amount |
| % Variance | Prefix with `Δ%` | Δ% Net Sales |
| Ratio/Percentages | Always end with `%` | Gross Margin % |
| Amount | Currency, 0–2 decimals | € #,##0.00 |
| Qty / Count | Integer | 0 |
| % | 1–2 decimals | 0.0 % |
| Display Folder | Domain grouping | e.g., "Sales", "Margin", "Working Capital" |

---

### QA & Governance Standards

- **Referential Integrity:** ≥ 99.9 % on Date/Org/Product.  
- **Variance Validation:** Δ (Price + Volume + Mix) ≈ Total Δ Net Sales (tolerance < 0.5 %).  
- **Plan Alignment:** All Plan data must include version ID.  
- **Currency:** Default EUR; FX at transaction date.  
- **Refresh:** Must match declared cadence (daily/weekly/etc.).

---

### Integration & Automation

The schema supports:
- Automated DAX generation.  
- Validation scripts (QA, RI, KPI health).  
- Documentation export into semantic model README.  
- Cross-Use Case lineage tracking via `domain_tag` and `use_case_ref`.

---

_This schema is mandatory for all KPIs added to `KPI_Catalog.md`.  
Any deviation will be flagged during catalog validation._

---

_Last updated: 08.10.2025_
