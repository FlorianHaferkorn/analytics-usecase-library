# Aurora Group Showcase

> **Scope:** Company profile, operating model, and synthetic gold data only.
> Semantic models and reports are **not** stored here — they live in `products/fabric/powerbi/dist/`.

Purpose: Demonstrate the ActionReady Analytics Framework with a **realistic synthetic company**. Aurora is tool-agnostic: company profile, operating model, and gold data. Report creation, semantic models, and pipeline live under the **tool-specific product** (e.g. Fabric: `products/fabric/powerbi/`).

## What Aurora contains

```yaml
aurora_group/
  company/     # Fictive company: profile, operating model, org chart
  data/        # Synthetic gold layer (Parquet/Delta)
    gold/      # fact_*, dim_* (see data/scripts/README.md to generate)
    scripts/   # Gold data generators (Python); run from repo root
  usecases/    # Demo scope: pointers to canonical core/usecases/core
```

## Where is what (repo)

| What | Location |
|------|----------|
| **Framework spec** | `core/strategy_operating_model/` |
| **Use case specs** | `core/usecases/core/` |
| **KPI catalog** | `core/kpi_catalog/` |
| **Generated TMDL & reports** (Fabric) | `products/fabric/powerbi/dist/` |
| **Fabric pipeline & docs** | `products/fabric/powerbi/orchestrator/`, `products/fabric/powerbi/docs/` |
| **Stage 1 (CI gate)** | `tooling/run_stage1_checks.ps1` |

## What we validate with Aurora

Can someone take a framework use case, use Aurora’s data (and a tool’s semantic model/report), and get the promised KPIs and data-driven decisions?

- **Stage 1 green** — `.\tooling\run_stage1_checks.ps1`
- **Aurora data** — Gold under `showcases/aurora_group/data/gold/`
- **Open PBIP** — Semantic model and reports from `products/fabric/powerbi/dist/` (see Fabric docs for how to run the pipeline and open reports)

**How to run the pipeline and verify:** See `products/fabric/powerbi/docs/DEMO_AND_VERIFICATION.md`.

## How to use Aurora

- Start with `company/Aurora_Group_Profile.md` and `company/Aurora_Operating_Model.md`.
- Generate gold data from repo root (see `data/scripts/README.md`). Point the Fabric semantic model/dataset to this path (or deployed equivalent).
- Align use cases with canonical factsheets in `core/usecases/core/`.
- Feed real KPI numbers into ALUCA Studio: run `python showcases/aurora_group/data/build_kpi_snapshot.py`. It aggregates the gold facts (DuckDB over the partitioned parquet) into `studio/data/aurora_kpi_snapshot.json`, keyed by `kpi_id`. Studio's report builder hydrates KPI cards, trends, and waterfalls from this snapshot, so exports show governed Aurora values instead of stub zeros. Regenerate after the gold data changes.

Relations: WHY → `company/`; HOW → `core/strategy_operating_model/`; WITH WHAT → Action Codes, KPI catalog; PATTERNS → `core/templates/page_templates/`.
