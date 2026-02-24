# Aurora Demo & Framework Package 1 Readiness

Purpose: One-page checklist and known blockers for running the Aurora demo and for considering Framework Package 1 “customer-ready” (PBIP opens, pipeline reproducible, docs in place).

---

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| **Power BI Desktop** | Current supported version; PBIP format. Open `.pbip` or report folder. |
| **Repo root as working directory** | All scripts and paths are relative to the repository root. |
| **Stage 1 one-time** | `cd tooling\validation` then `npm ci` (for schema validation). |
| **Python 3** | Required for report generation (page_scaffold_generator). If missing, orchestrate falls back to a simpler report structure. |
| **Node** | Only if you run tooling that depends on it (e.g. schema validation). |

---

## Demo run (numbered steps)

1. **Stage 1 (CI gate):** From repo root run `.\tooling\run_stage1_checks.ps1`. Fix any failures before continuing.
2. **Pipeline:** Run `.\tooling\powerbi_mcp\orchestrate_full_model.ps1 -All` (or `-Domain Commercial` / `-UseCase COM-001`). This builds the registry, generates measures into the Aurora semantic model, and generates reports under `products/fabric_powerbi/dist/<UC>.Report`.
3. **Gold data (optional):** If you need live data for the model, run the gold data scripts as in `showcases/aurora_group/README.md` (e.g. `py showcases/aurora_group/data/scripts/generate_aurora_gold.py`). Point the semantic model/dataset to the gold path if required.
4. **Open PBIP:** Open a domain semantic model (e.g. `showcases/aurora_group/semantic_models/Commercial.SemanticModel`) or a generated report: `products/fabric_powerbi/dist/<UC>.Report`. Each report’s dataset reference points to its domain model (e.g. COM-001 → Commercial.SemanticModel). See `products/fabric_powerbi/docs/fabric_powerbi.md` §3.4 and §3.5.

---

## Known blockers / limits

- **RLS:** Row-Level Security (e.g. user–org mapping) is not applied automatically; configure manually if required.
- **Publish to Fabric:** No automated publish to Fabric service; deploy/Publish from Desktop or use your own deployment pipeline.
- **Power BI Desktop only:** This readiness scope is “opens in Desktop and loads”; no claim for Fabric workspace deployment or embedding.

---

## What “customer-ready” means for Framework Package 1

- **PBIP and reports open** in Power BI Desktop without errors.
- **Pipeline is reproducible:** Single source (`core/usecases/core`), three modes (`-UseCase`, `-Domain`, `-All`), no hardcoded use-case lists.
- **Documentation present:** How to reproduce (Aurora README), how to open reports (§3.4–3.6 in fabric_powerbi.md), verification steps, and this readiness checklist.
- **No known blockers** for the defined demo scope (open PBIP, load report, see scaffolded pages). Limits (RLS, Publish) are documented above.

---

## Reproducibility proof (add one use case)

To confirm the pipeline works with any use case from the single source (`core/usecases/core`):

1. Add a new use case (e.g. via `.\tooling\generation\new_usecase.ps1`) or use an existing one that is not yet in the list discovered from the root. Ensure it has a folder `ID_Title` and a valid `UseCase_Bracket.yaml`.
2. Update registry/inventory if your process requires it (Stage 1 and orchestrate run the registry builder).
3. Run `.\tooling\powerbi_mcp\orchestrate_full_model.ps1 -All`.
4. Confirm the new use case’s report appears under `products/fabric_powerbi/dist/<ID>.Report` and that the Aurora semantic model’s `_Measures.tmdl` includes measures for that use case (e.g. displayFolder for the new ID).

This proves the pipeline is driven solely by the contents of the use-case root, with no hardcoded scope.
