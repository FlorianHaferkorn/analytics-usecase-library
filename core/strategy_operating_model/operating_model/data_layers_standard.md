# Data Layers Standard (Tool-Agnostic)

**Purpose:** Single reference for the standard data layers used by the framework. Defines what we **define** vs what we **deliver** and keeps the procedure Silver-first.

---

## 1. Architecture Layers (4 Physical + 1 Logical)

| Layer | Type | Description |
|-------|------|-------------|
| **Staging / Landing** | Physical | Transient landing for raw extracts. Minimal validation. |
| **Bronze** | Physical | Persisted raw, source-aligned data with full lineage and history. |
| **Silver** | Physical | Conformed, validated domain data with standardized keys and types. |
| **Gold** | Physical | Curated, consumption-ready structures for analytics (e.g. star schema). |
| **Semantics** | Logical | KPI catalog, measure logic, action codes, semantic model definitions. |

### 1.1 Layer Definitions (What Each Layer Is)

| Layer | Definition |
|-------|------------|
| **Staging** | Raw payloads land here with minimal or no validation. Transient; often overwritten or cleared. Purpose: quick ingest and hand-off to Bronze. |
| **Bronze** | Immutable, persisted copy of source data. Same structure and format as source (or trivial parse). Full history and lineage; append or version. Optimized for durability and reprocessing, not query. Source of truth for “what we received.” |
| **Silver** | Conformed, validated domain data. Standardized keys, types, and names; quality rules applied; one grain per entity (e.g. invoice line, customer-month). May still be normalized or at transaction grain. Single domain-level source of truth for “clean” data. **Defined by data contracts** (schema, grain, refs). Optimized for consistency and reuse. |
| **Gold** | Consumption-ready layer for analytics and semantics. Star (or snowflake) schema; conformed dimensions; facts at analytical grain (same or coarser than Silver); may include pre-built **action aggregates** (e.g. deviation, thresholds). Subset or derivation of Silver. Optimized for query performance and for the semantic layer. |

---

## 2. Project Coverage (What We Define vs Deliver)

- **We define Silver** via contracts (domain-level; see `core/data_contracts/domains/`). Contracts specify schemas, grains, keys, and quality expectations for conformed domain data.
- **We deliver Gold + Semantics** via report packages and semantic models. Gold is derived from Silver (consumption-ready). Semantics (measures, KPIs) consume Gold.
- **Staging and Bronze are out of scope** unless explicitly included (e.g. a customer or engagement adds them).

**Procedure:** Start from Silver. Define or adopt Silver contracts; then build Gold and the semantic layer from that. Do not start from Gold-only.

---

## 3. Flow

```
[Sources] → Staging (optional) → Bronze (optional) → Silver ← contracts define
                                                          ↓
                                              Gold (derived from Silver)
                                                          ↓
                                              Semantics (measures, reports)
```

---

## 4. Silver vs Gold (In Practice They Differ)

**In reality Silver and Gold will usually differ.** Treating them as the same is a simplification for demos; production implementations should separate them.

| Aspect | Silver | Gold |
|--------|--------|------|
| **Purpose** | Conformed, validated domain data; single source of truth for “clean” operational/domain shape. | Consumption-ready structures for analytics and semantics. |
| **Schema** | Defined by data contracts (domain grain, full column set, keys, refs). May be normalized or transaction-level. | Star/snowflake schema; may be aggregated, subset of columns, derived tables (e.g. action aggregates). |
| **Grain** | Contract grain (e.g. invoice line, customer-month). | May match Silver or be coarser (e.g. product-month, week) for performance. |
| **Content** | Facts and dimensions as per contract; no pre-calculated action flags. | Same or derived facts; conformed dimensions; **action aggregates** (deviation, thresholds) for reporting. |
| **Defined by** | `core/data_contracts/domains/*.yaml` (and sources). | Gold schema/layout per `lakehouse_architecture.md`; **Silver→Gold transformation** (mapping, aggregation rules) should be defined per domain or in a standard. |

**Transformation:** Silver → Gold is a defined step (ETL/ELT or views): filter columns, change grain, add action aggregates, enforce star layout. That mapping is not yet fully standardized in this repo; it should be documented or versioned per domain so Gold is reproducible from Silver.

---

## 5. Standardizing Silver → Gold (Same Setup Every Time)

To make Silver → Gold **repeatable and always the same to set up**, use a fixed pattern and a single mapping contract per domain (or per solution).

### 5.1 Standard Gold Layout (Fixed)

- **Folders:** `gold/dimensions/`, `gold/facts/`, `gold/action_aggregates/` (see `lakehouse_architecture.md`).
- **Naming:** `dim_*`, `fact_*`, `agg_*` for action aggregates.
- **Format:** Delta Parquet; partitioning and z-order per lakehouse doc.

Every project uses this layout so tooling and semantics can assume the same structure.

### 5.2 Standard Transformation Pattern (Fixed)

| Gold artifact | Rule | Notes |
|---------------|------|--------|
| **Dimensions** | 1:1 from Silver dimensions, or conformed merge from multiple Silver dims. Same name in Gold unless conformed (e.g. `dim_org`). Column list can be subset; keys and refs must be consistent. | No grain change. |
| **Facts** | One Gold fact per Silver fact **or** one Gold fact per analytical grain (e.g. Silver `fact_sales` at invoice line → Gold `fact_sales` at same grain, or Gold `fact_sales_monthly` at product-month). Explicit: source Silver table(s), grain, column mapping or aggregation. | Document grain and aggregation (sum, avg, etc.) per measure. |
| **Action aggregates** | One Gold `agg_*` per action-code family or deviation type. Source: Silver facts + (optional) dimensions. Schema: keys (e.g. DateKey, ProductKey), deviation/flag columns (e.g. L1_Flag, L2_Flag), and metrics. Tied to `core/action_codes/`. | Standard pattern: same key structure as related fact; add threshold flags and deviation amounts. |

Apply this pattern everywhere so pipelines and semantics know what to expect.

### 5.3 Silver–Gold Mapping Contract (Per Domain / Per Solution)

Define the concrete mapping in **one place per domain** (or per solution) so setup is reproducible:

- **What:** A declarative mapping that lists, for each Gold table: source Silver table(s), grain (if different), column list or aggregation rules, and type (dimension | fact | action_aggregate).
- **Where:** Use the template `core/templates/silver_to_gold/silver_to_gold_mapping_template.yaml`; fill one file per domain (e.g. `commercial_silver_to_gold.yaml`) or one combined file. Store under `core/data_contracts/` (e.g. `data_contracts/silver_to_gold/`) or in the solution repo.
- **Use:** ETL/ELT or codegen reads this mapping and generates pipelines or SQL so Gold is always built the same way from Silver.

The template ensures every project has the **same structure** to fill in (dimensions, facts, action_aggregates with source, grain, columns), so setup is identical and tooling can validate or generate from it.

### 5.4 Checklist for Repeatable Setup

1. **Silver contracts** exist for the domain (`data_contracts/domains/*.yaml`).
2. **Gold layout** follows the standard (`gold/dimensions/`, `gold/facts/`, `gold/action_aggregates/`).
3. **Silver–Gold mapping** file is created from the template; every Gold table has a defined source, grain, and column/aggregation rule.
4. **Action aggregates** are listed with their source fact(s) and linked action code(s).
5. **Pipeline or views** are generated or implemented from the mapping so Gold is reproducible from Silver.

---

## 6. Standardization Status

| Link | Standardized? | Where / gap |
|------|----------------|-------------|
| **Silver** | Yes | Domain contracts (`core/data_contracts/domains/*.yaml`) define Silver schema, grain, keys, refs. |
| **Silver → Gold** | Partially | Gold **structure** (folders, format, partitioning) is in `lakehouse_architecture.md`. **Transformation rules** (how Silver maps to Gold: columns, grain, action aggregates) are not yet a single standard; they should be defined so Silver and Gold can legitimately differ in real implementations. |
| **Gold → Semantics** | By convention | Semantic model (TMDL, blueprint) aligns with Gold table/column names. No single Gold→Semantics interface doc. |

**Showcase note:** The synthetic generator and some docs assume contract schema ≈ Gold schema (1:1) for simplicity. Real projects should treat Silver (contract) as the source of truth and Gold as a derived, consumption layer with its own schema and transformation.

---

## 7. Relations

- **Silver contracts:** `core/data_contracts/domains/`, `core/data_contracts/sources/`
- **Silver–Gold mapping template:** `core/templates/silver_to_gold/silver_to_gold_mapping_template.yaml` (repeatable setup)
- **Lakehouse implementation:** `lakehouse_architecture.md` (Silver → Gold structure, Gold layout and format)
- **Semantic layer:** `semantic_layer.md`, `measure_system.md` (legacy blueprint archived to internal/archive/legacy_action_ready_and_blueprint_2026-02/)
- **Playbook:** `core/implementation_guides/playbook_strategy_to_first_report.md` (Step 3: Silver contracts)

---

## 8. Sources & Grounding

The layered model in this standard is the industry **medallion (lakehouse) architecture** —
Bronze (raw) → Silver (validated/conformed) → Gold (consumption-ready) — with a Kimball
dimensional model at the Gold layer. Grounded in:

- **Medallion lakehouse architecture** (origin of the bronze/silver/gold quality-layer pattern) —
  Databricks: <https://docs.databricks.com/aws/en/lakehouse/medallion> · Microsoft Learn
  (Azure Databricks): <https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion> ·
  Microsoft Fabric OneLake:
  <https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture>
- **Gold-layer dimensional modelling** (star schema, conformed dimensions) — Kimball Group,
  Dimensional Modeling Techniques:
  <https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/>

> This framework deliberately *defines Silver* (via data contracts) and *delivers Gold + Semantics*;
> Staging/Bronze are out of scope unless a project adds them (see §2).

---

**Location:** `core/strategy_operating_model/operating_model/data_layers_standard.md`
