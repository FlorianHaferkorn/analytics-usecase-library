# Fabric Orchestrator (Builder Engine)

Orchestration and report generation for semantic models and reports (PBIP) from UseCase Brackets and KPI Catalog. Run from **repository root**.

## Prerequisites

- PowerShell 7+
- Python 3.x (for Registry, page_scaffold_generator)
- Optional: Node/npm in `tooling/validation` for schema validation

## Setup (once)

1. **Registry and contracts:** Ensure Stage 1 passes so `tooling/ontology/out/master_registry.json` exists:
   ```powershell
   .\tooling\run_stage1_checks.ps1
   ```
2. **Connections:** Create `products/fabric_powerbi/orchestrator/connections.json` (e.g. via setup_connection.ps1) if you use table_ops/relationship_ops with a named connection.
3. **Python deps for UX Engine:** For full reports (overview + detail) with visuals:
   ```powershell
   pip install -r products/fabric_powerbi/tooling/page_scaffold_generator/requirements.txt
   ```

## Build

**One command – Use Case:**
```powershell
.\products\fabric_powerbi\orchestrator\orchestrate_full_model.ps1 -UseCase COM-001
```

**One command – Domain (e.g. Commercial, all COM-001..004):**
```powershell
.\products\fabric_powerbi\orchestrator\orchestrate_full_model.ps1 -Domain Commercial
```

**Mit Aurora-Daten (gefüllte Tabellen):** Ohne `-UseAuroraData` erhalten Tabellen eine leere Partition (Blank). Für Bezug zu den Aurora-Gold-Parquet-Daten den Lauf mit `-UseAuroraData` ausführen; dann werden die Partitionen auf `GoldDataPath` umgestellt, `expressions.tmdl` enthält den Parameter `GoldDataPath`, und die Reports zeigen Daten, sofern der Gold-Pfad (`showcases/aurora_group/data/gold`) und die Parquet-Dateien verfügbar sind:
```powershell
.\products\fabric_powerbi\orchestrator\orchestrate_full_model.ps1 -UseCase COM-001 -UseAuroraData
```
**Semantisches Modell vollständig:** `definition/model.tmdl` muss für jede Tabelle in `definition/tables/` eine Zeile `ref table <Tabellenname>` enthalten. Der Orchestrator ergänzt fehlende refs automatisch (Schritt „Sync model.tmdl refs“). Fehlen refs, lädt Desktop das Modell unvollständig.

- Build runs **Registry** first, then measures, tables/relationships/hierarchies, validation, and **report generation** (UX Engine: overview + detail per use case, with `datasetReference`).
- If Python 3 is missing, report generation falls back to report_generator.ps1 (sections only, no visuals).
- **Quality checks are a hard gate:** any ERROR/FAIL from `run_all_checks.ps1` fails the build.

**Output (single Fabric dist):**

- **Semantic models:** `products/fabric_powerbi/dist/<Domain>.SemanticModel` (e.g. `Commercial.SemanticModel`). Contains `definition/` (model.tmdl, tables/*.tmdl, expressions.tmdl) and `definition.pbism`; **no** `.pbip` for the semantic model (only reports have `.pbip`).
- **Reports:** `products/fabric_powerbi/dist/<UseCase>_<Title>.Report` (e.g. `COM-001_Sales_Performance.Report`); each report’s `datasetReference` points to its domain model in the same dist.

**Dist structure (no legacy folders):** Only `<Domain>.SemanticModel` and `<UseCase>_<Title>.Report`. There is no `dist/COM-001/` (per-use-case semantic model) and no `dist/_shared/`; measure generation writes directly into the domain model’s `definition/tables/` (via `-TargetTablesDir` in the orchestrator or derived from `-UseCase` when running the measure script standalone).

**Gate (success = no manual Desktop open required):** After report generation, the pipeline runs **Validate Fabric output**: (1) `run_fabric_checks.ps1` (TMDL, PBIP readiness, DAX, measures vs KPI), (2) `check_report_structure.ps1` and `validate_pbip.ps1`, (3) if installed, `pbi-tools compile` on each PBIP folder. Success means all phases PASS. See [products/fabric_powerbi/docs/DEMO_AND_VERIFICATION.md](../docs/DEMO_AND_VERIFICATION.md).

## Adding a new use case to an existing domain (incremental)

To add a new use case (e.g. COM-005) to an existing domain model without duplicating measures or breaking reports:

1. **Create the use case** in `core/usecases/core` (folder `COM-005_<Title>`, `UseCase_Bracket.yaml`, optional `Business_Factsheet.md`). Ensure it has `orchestration.action_code_ids` and KPI references that exist in the catalog.
2. **Run orchestrate with the same domain** (or `-All`):  
   `.\products\fabric_powerbi\orchestrator\orchestrate_full_model.ps1 -Domain Commercial`  
   The pipeline discovers all use cases from the root; for Commercial it will now include COM-005. Measure generation writes **one** `_Measures.tmdl` per domain with **all** use cases in scope (displayFolder per use case). No separate merge step; re-run overwrites with the full set, so no duplicate measure names per folder.
3. **Check output:** `products/fabric_powerbi/dist/Commercial.SemanticModel` contains updated `_Measures.tmdl`; `products/fabric_powerbi/dist/COM-005.Report` is created. Run the **Validate Fabric output** phase (automatic) to confirm TMDL and, if pbi-tools is installed, compile.

**Note:** The pipeline does not “append” to an existing _Measures.tmdl; it regenerates from the current scope. To add a use case, include it in scope (by adding it to the repo and using `-Domain` or `-All`).

## Deploy

```powershell
.\products\fabric_powerbi\orchestrator\deploy.ps1
```

- Runs **deploy_gate.ps1** (contracts + registry, zero-tolerance).
- Fabric Workspace / Import Model / Import Report are still **stubs** (see [internal/technical_backlog.md](../../../internal/technical_backlog.md) § Power BI MCP). Configure `FABRIC_WORKSPACE_ID` or `FABRIC_WORKSPACE_NAME` and implement API calls (e.g. FabricPS-PBIP) as needed.

## Phase 2 (Builder Engine)

- Measure/Dimension binding in visuals (queryState from Registry/TMDL, `ux_bindings` overrides).
- Action Codes in 30s Teaser and 300s Action Panel (from Bracket `action_code_ids`).
- Streamlit UX Layout Editor: Tabs for **Bindings** and **Actions**; write `ux_bindings` to Bracket.
- deploy.ps1: real Fabric API (Workspace, Import Model, Import Report + binding).
- See [internal/vision/phase2_backlog.md](../../../internal/vision/phase2_backlog.md) and plan "Builder Engine Phase 1".
