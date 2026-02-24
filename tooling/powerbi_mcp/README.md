# Power BI MCP / Builder Engine

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
2. **Connections:** Create `tooling/powerbi_mcp/connections.json` (e.g. via setup_connection.ps1) if you use table_ops/relationship_ops with a named connection.
3. **Python deps for UX Engine:** For full reports (overview + detail) with visuals:
   ```powershell
   pip install -r products/fabric_powerbi/tooling/page_scaffold_generator/requirements.txt
   ```

## Build

**One command – Use Case:**
```powershell
.\tooling\powerbi_mcp\orchestrate_full_model.ps1 -UseCase COM-001
```

**One command – Domain (e.g. Commercial, all COM-001..004):**
```powershell
.\tooling\powerbi_mcp\orchestrate_full_model.ps1 -Domain Commercial
```

- Build runs **Registry** first, then measures, tables/relationships/hierarchies, validation, and **report generation** (UX Engine: overview + detail per use case, with `datasetReference`).
- If Python 3 is missing, report generation falls back to report_generator.ps1 (sections only, no visuals).
- **Quality checks are a hard gate:** any ERROR/FAIL from `run_all_checks.ps1` fails the build.

**Output:**

- Semantic model: per domain, e.g. `showcases/aurora_group/semantic_models/Commercial.SemanticModel`
- Reports: `products/fabric_powerbi/dist/<UseCase>.Report` (e.g. COM-001.Report)

## Deploy

```powershell
.\tooling\powerbi_mcp\deploy.ps1
```

- Runs **deploy_gate.ps1** (contracts + registry, zero-tolerance).
- Fabric Workspace / Import Model / Import Report are still **stubs** (see [internal/technical_backlog.md](../../internal/technical_backlog.md) § Power BI MCP). Configure `FABRIC_WORKSPACE_ID` or `FABRIC_WORKSPACE_NAME` and implement API calls (e.g. FabricPS-PBIP) as needed.

## Phase 2 (Builder Engine)

- Measure/Dimension binding in visuals (queryState from Registry/TMDL, `ux_bindings` overrides).
- Action Codes in 30s Teaser and 300s Action Panel (from Bracket `action_code_ids`).
- Streamlit UX Layout Editor: Tabs for **Bindings** and **Actions**; write `ux_bindings` to Bracket.
- deploy.ps1: real Fabric API (Workspace, Import Model, Import Report + binding).
- See [internal/vision/phase2_backlog.md](../../internal/vision/phase2_backlog.md) and plan "Builder Engine Phase 1".
