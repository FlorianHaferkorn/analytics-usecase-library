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

---

## 2. Project Coverage (What We Define vs Deliver)

- **We define Silver** via contracts (domain-level; see `framework/data_contracts/domains/`). Contracts specify schemas, grains, keys, and quality expectations for conformed domain data.
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

## 4. Standardization Status (Outcome Expected)

What is **already standardized** for Silver → Gold → Semantics:

| Link | Standardized? | Where |
|------|----------------|--------|
| **Silver** | Yes | Domain contracts (`framework/data_contracts/domains/*.yaml`) define schema, grain, columns, keys, refs. Same structure for all conformed domain data. |
| **Silver → Gold** | Yes (outcome) | Gold implements the contract: same entity names (dim_*, fact_*), same grain and columns. Lakehouse doc: "gold layer structure implements data contracts" (§8). Synthetic generator is contract-compliant and writes to Gold. So: **contract schema = Gold schema** by design. |
| **Gold → Semantics** | By convention | Semantic model (TMDL, blueprint) uses same table and column names as Gold/contract. Measure system and KPI catalog govern measures. No single "Gold-to-Semantics interface" doc; alignment is via naming and blueprint (`ActionReady_SemanticModel_Blueprint.md`). |

**Implications:**

- **Silver:** The contract *is* the Silver standard. There is no separate "Silver storage format" in scope; when we say "Silver" we mean the conformed domain data as specified by the contract (and, when implemented, typically instantiated as Gold with that schema).
- **Gold:** Standardized as "contract implementation": Delta Parquet, `gold/dimensions/`, `gold/facts/`, `gold/action_aggregates/`, partitioning and format per `lakehouse_architecture.md`.
- **Semantics:** Expected outcome (star schema, conformed dimensions, measures from KPI catalog) is standardized; exact table/column list per domain is in the blueprint and semantic model READMEs, not in one Gold→Semantics contract file.

**Gaps (if we want stricter standardization later):**

- Explicit "Silver storage" spec only needed if Silver and Gold ever differ (e.g. Silver has extra columns, Gold is a subset). Today they are 1:1.
- A single **Gold-to-Semantics interface** document (required Gold tables/columns per domain for semantic model binding) would make the expected outcome machine-checkable.

---

## 5. Relations

- **Silver contracts:** `framework/data_contracts/domains/`, `framework/data_contracts/sources/`
- **Lakehouse implementation:** `lakehouse_architecture.md` (Silver → Gold structure, Gold layout and format)
- **Semantic layer:** `semantic_layer.md`, `measure_system.md`, `reference/ActionReady_SemanticModel_Blueprint.md`
- **Playbook:** `framework/implementation_guides/playbook_strategy_to_first_report.md` (Step 3: Silver contracts)

---

**Location:** `framework/strategy_operating_model/operating_model/data_layers_standard.md`
