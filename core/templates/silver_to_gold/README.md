# Silver → Gold Mapping Template

**Purpose:** Standardize how Silver is mapped to Gold so every project sets up the same way.

## What this is

- A **template YAML** (`silver_to_gold_mapping_template.yaml`) that defines the structure of the Silver–Gold mapping.
- One **mapping file per domain** (or one per solution) filled from this template: lists Gold dimensions, facts, and action aggregates with their Silver source(s), grain, and column/aggregation rules.
- Used so **ETL/ELT or codegen** can produce Gold from Silver in a repeatable way.

## What this is not

- Not the Silver data contract (that is `data_contracts/domains/*.yaml`).
- Not the physical pipeline code; it is the **declarative spec** that pipelines or views implement.

## Usage

1. Copy `silver_to_gold_mapping_template.yaml` to your domain or solution (e.g. `commercial_silver_to_gold.yaml`).
2. Fill in for each Gold table: `silver_source` (or `silver_sources`), `grain`, and for facts/aggregates any `measures` or `deviation_columns`.
3. Store under `core/data_contracts/silver_to_gold/` (if framework-wide) or in the solution repo.
4. Use the mapping as input to pipeline generation or as the single source of truth for Silver→Gold transformation.

## Standard pattern (reference)

- **Dimensions:** 1:1 from Silver or conformed merge; same name unless conformed.
- **Facts:** One Gold fact per Silver fact at same grain, or one per analytical grain with explicit aggregation.
- **Action aggregates:** One `agg_*` per action-code family; keys + L1/L2/L3 flags + deviation columns; linked to `core/action_codes/`.

See `core/strategy_operating_model/operating_model/data_layers_standard.md` (§5).

---

**Location:** `core/templates/silver_to_gold/`
