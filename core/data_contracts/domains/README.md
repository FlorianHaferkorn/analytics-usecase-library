# Domain Data Contracts

## Purpose

Define the **Silver layer** (canonical, conformed domain data) for each business domain within the ActionReady Analytics Framework. These contracts formalize the structure, grain, units, keys, and lineage that **Silver** must satisfy; Gold and semantic models are built from Silver.

Domain Data Contracts ensure:

- stable schemas,
- consistent semantics,
- predictable ingestion into semantic models,
- and full cross-domain interoperability.

## Scope

Included:

- YAML-based data contracts for Sales, Finance, SCM, ESG, and others  
- Mandatory fields per fact and dimension  
- Grain definitions and surrogate key requirements  
- Unit rules, format rules, and data categories  
- Lineage metadata per field

Not included:

- Transformation logic (ETL/Dataflows/Data Pipelines)  
- Customer-specific data structures  
- Semantic model definitions (see `core/semantic_models/`)  

## Structure

```yaml
core/data_contracts/
  domains/
    commercial_sales.yaml
    finance.yaml
    supply_chain.yaml
    operations.yaml
    experience.yaml
    executive.yaml
    README.md  # this file
```

Each domain file contains:

- **Dimensions** (keys, names, hierarchies)  
- **Facts** (grain, metrics, units)  
- **Integrity expectations**  
- **Lineage metadata**  

Example snippet:

```yaml
fact:
  - name: fact_sales
    grain: invoice_line
    columns:
      - {name: DateKey, type: date_key, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Net Sales Amount, type: currency, agg: sum}
```

### Structured quality fields (A-20/A-23, 29.09.2026)

Rules that a machine can run live **on the column**, not as prose in `quality_rules`
(consumed by `tooling/generator/export_governed_catalog.py` → `column_specs`, checked by
`tooling/validation/check_validate_data_contracts.py`):

| Field | Where | Meaning |
|---|---|---|
| `nullable` | column | `true` = NULL allowed. Missing = never NULL. |
| `ref` | column | FK to the dimension's `role: key` column. |
| `unknown_member: <value>` | FK column | Never NULL; `<value>` (e.g. `-1`) is the placeholder row of the referenced dimension ("unknown"/"none"). `nullable` is then `false`. |
| `source_column: <name>` | column | Physical Gold column when `name` is the business/model name (the TMDL `column` + `sourceColumn` split), e.g. `{name: Sales Units, source_column: Quantity}`. Checks and the showcase proof run against `source_column`; the linguistic schema binds `name`. |
| `checks: [...]` | column | List of entries with exactly one of `gte`, `gt`, `lte`, `lt` (number), `between: [a, b]` (inclusive), `in: [...]` (allowed values), `gte_column` / `lte_column` (another column of the same row), optionally `when_present: true`. Example: `checks: [{between: [0, 10]}]`. |
| `target_state: true` | column | Target design: not (yet) delivered by the Aurora showcase or read by a model. |
| `showcase: false` | table | The Aurora showcase has no data for this table (missing = present). |

Semantics: without `when_present`, a NULL value violates a check; with it, only non-NULL values
are checked. For `*_column`, a NULL on the compared side cannot be evaluated and does not count
as a violation. `quality_rules` keeps `freshness_sla` and only what does not structure
(arithmetic across columns, business meaning of NULL, lineage notes).

Proof against Aurora gold: `tooling/tests/test_contract_rules_showcase.py` (counts rules run,
not in showcase, and column missing in gold).

## Usage

### For Customers

- Validate whether existing systems can supply the required data  
- Understand what “good” analytical data looks like per domain  
- Support IT ↔ BI alignment through clear contracts

### For Delivery Teams

- Use domain contracts as stable input for ingestion layers  
- Map customer systems to the standardized domain structure  
- Guarantee consistent downstream semantic models  
- **Semantic model alignment:** The semantic model (e.g. Fabric TMDL tables) is built from these contracts. KPI catalog entries reference contract tables/columns via `technical.lineage`. When a use case requires a KPI, the contract must define the tables and columns that KPI’s lineage references (e.g. `fact_sales` with `List Price Amount`, `Net Price Amount` for Price Realization %).  

### For Framework Evolution

- Add new contracts only when domain boundaries expand  
- Maintain backward compatibility where possible  

## Relations

- **WHY Contracts derive from domain definitions in `core/strategy_operating_model/company/domains.md`  
- **HOW Semantic layer rules enforce contracts during modeling  
- **WITH WHAT Measure TEMPLATES, naming rules, and KPI Catalog rely on contract structure  
- **TEMPLATES** Fact and dimension templates live under `core/templates/data_contract_templates/`.

**Location:**  
`core/data_contracts/domains/README.md`
