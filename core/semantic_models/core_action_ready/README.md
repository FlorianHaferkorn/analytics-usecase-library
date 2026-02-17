# Core Action-Ready Semantic Model

> **Canonical blueprint:** [ActionReady_SemanticModel_Blueprint.md](../../strategy_operating_model/operating_model/reference/ActionReady_SemanticModel_Blueprint.md).  
> This implementation must align with the blueprint; it does not redefine the conceptual model.

## Purpose

Canonical action-ready semantic model that implements **governed KPIs and measures** for use cases and reports.  
It does **not** define KPI meaning; that lives in `core/kpi_catalog/` (KPI Catalog). This model provides the **computable layer** that references KPI IDs and follows measure patterns from the catalog.

## SSOT and inputs

- **KPI definitions:** `core/kpi_catalog/KPI_Catalog.md` (authoritative).
- **Active set (use cases, KPIs, action codes):** `tooling/ontology/out/master_registry.json` (built by `registry_builder.py` from UseCase_Bracket.yaml and action codes).
- **Measure generation:** `tooling/generation/generate_tmdl_measures.ps1` uses the master registry to organize measures; run from repo root after registry build.

## Scope

- **In scope:** `model_definition.yaml`, measure definitions (TMDL or measure dictionaries) that reference KPI IDs from the catalog.
- **Out of scope:** Draft or domain-specific experimental models; those live under `core/semantic_models/domains/` where applicable.

## Structure

- `model_definition.yaml` — high-level model name, version, purpose.
- `measures/` (or generated TMDL) — canonical measures aligned with KPI catalog and active use cases.

## When to update

- When KPIs or measure logic change in the **KPI Catalog** (update catalog first, then align measures here).
- When new core use cases or action codes are added (registry and TMDL generation will reflect them).
- When measure naming or aggregation rules are standardized (update templates and this model consistently).

## Relations

- **Feeds:** Use cases (via reports and semantic layer), showcase reports, and any consumer of the action-ready measure set.
- **Consumes:** KPI Catalog, `master_registry.json`, data contracts for grain and lineage.

## Usage

- Use as the baseline semantic model for Power BI / Fabric and other tools that consume the action-ready measure set.
- Do not duplicate KPI definitions here; reference `kpi_id` and keep logic consistent with the catalog.
