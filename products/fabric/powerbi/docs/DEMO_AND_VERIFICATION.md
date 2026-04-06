# Fabric Demo & Verification

One-page checklist for running the Fabric pipeline and verifying PBIP output (Aurora showcase uses this; run from **repo root**).

---

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| **Power BI Desktop** | Current supported version; PBIP format. Open `.pbip` or report folder. |
| **Repo root as working directory** | All scripts and paths are relative to the repository root. |
| **Stage 1 one-time** | `cd tooling\validation` then `npm ci` (for schema validation). |
| **Python 3** | Required for report generation (page_scaffold_generator). On Windows usually invoked via `py -3`. If no Python is found, orchestrate falls back to a simpler report structure. |
| **Node** | Only if you run tooling that depends on it (e.g. schema validation). |

---

## Pipeline (numbered steps)

1. **Stage 1 (CI gate):** From repo root run `.\tooling\run_stage1_checks.ps1`. Fix any failures before continuing.
2. **Fabric pipeline:** Run the orchestrator with one of:
   - **All use cases:** `.\products\fabric/powerbi\orchestrator\orchestrate_full_model.ps1 -All`
   - **One domain:** `.\products\fabric/powerbi\orchestrator\orchestrate_full_model.ps1 -Domain Commercial`
   - **Single use case:** `.\products\fabric/powerbi\orchestrator\orchestrate_full_model.ps1 -UseCase COM-001`
   Output: `products/fabric/powerbi/dist/<Domain>.SemanticModel` and `products/fabric/powerbi/dist/<UC>.Report`.
3. **Gold data (optional):** For Aurora, run e.g. `py showcases/aurora_group/data/scripts/generate_aurora_gold.py`. Point the semantic model/dataset to the gold path if required.
4. **Open PBIP:** Open a domain semantic model (e.g. `products/fabric/powerbi/dist/Commercial.SemanticModel`) or a report (`products/fabric/powerbi/dist/<UC>.Report`). See `fabric/powerbi.md` §3.4 and §3.5.

---

## Verification: PBIP loadable

The pipeline runs validation after report generation:

1. **Best-practice rules** — `run_fabric_checks.ps1` (TMDL, PBIP readiness, DAX, measures vs KPI).
2. **Structure** — `check_report_structure.ps1`, `validate_pbip.ps1` on each PBIP folder in dist.
3. **pbi-tools compile (optional)** — If [pbi-tools](https://pbi.tools) is installed, each dist folder is compiled. Failures in `products/fabric/powerbi/orchestrator/out/build_errors.json` and `last_run_state.json` under `validateErrors`.

**Manual playthrough (recommended once per scope change):**

1. From repo root run `.\products\fabric/powerbi\orchestrator\orchestrate_full_model.ps1 -Domain Commercial`.
2. Open `products\fabric/powerbi\dist\Commercial.SemanticModel` in Power BI Desktop. Resolve any DAX/data source errors; note in `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`.
3. Open `products\fabric/powerbi\dist\COM-001.Report` in Power BI Desktop. Confirm pages load and dataset reference resolves.

---

## Optional: pbi-tools

- **Install:** e.g. `winget install pbi-tools` or see [pbi.tools](https://pbi.tools).
- **Usage:** Orchestrator runs `pbi-tools compile <folder>` for each PBIP under `products/fabric/powerbi/dist`. CI-friendly (headless).

---

## Known limits

- **RLS:** Not applied automatically; configure manually if required.
- **Publish to Fabric:** Ein automatisierter Publish-Pfad existiert jetzt ueber products/fabric/powerbi/tooling/invoke_workspace_publish.ps1 plus deployment/scripts/fabric_release.py. Ohne Credentials oder Fabric-Zielumgebung bleibt das lokal ein Dry-Run und erfuellt den Produktionsstandard nicht.
- **Credentialloser Abnahmemodus:** Falls vorlaeufig keine Fabric-Credentials verfuegbar sind, kann invoke_production_supervisor.ps1 mit AcceptDryRunPublish laufen. Das validiert Build, Gates und Publish-Staging, markiert das Ergebnis aber explizit nur als credentialless_dry_run.
- **Scope:** "Opens in Desktop and loads"; no claim for Fabric workspace deployment or embedding.

---

## Reproducibility (add one use case)

1. Add a new use case in `core/usecases/core` (folder `ID_Title`, valid `UseCase_Bracket.yaml`).
2. Run `.\products\fabric/powerbi\orchestrator\orchestrate_full_model.ps1 -All`.
3. Confirm new report under `products/fabric/powerbi/dist/<ID>.Report` and measures in the domain `_Measures.tmdl`.

Scope is discovered from `core/usecases/core`; no hardcoded use-case list.
