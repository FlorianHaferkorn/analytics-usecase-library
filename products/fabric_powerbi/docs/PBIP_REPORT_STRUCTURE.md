# Canonical PBIP Report Folder Structure (Fabric Power BI)

This is the **Fabric Power BI product layout** for report and semantic-model PBIP folders. All generated output under `products/fabric_powerbi/dist/` must match it so Power BI Desktop and pbi-tools can open artifacts. Showcases (e.g. Aurora) follow the same layout; this doc is the single source of truth for the product.

## Report layout

```
<UseCase>.Report/
├── Report.pbip                    # pbipProperties: artifacts[].report.path = "."
├── definition.pbir                # Report properties: $schema definitionProperties/2.0.0, version, datasetReference; required by Desktop Feb 2026+
├── definition/
│   ├── report.json                # Fabric 3.0 schema; no datasetReference (schema disallows it; binding is in definition.pbir only)
│   ├── version.json               # version 1.0 (optional $schema)
│   └── pages/
│       ├── pages.json             # pageOrder, activePageName
│       └── Page_<UC>_<Name>/      # e.g. Page_COM001_Overview, Page_COM001_Detail
│           ├── page.json
│           └── visuals/
│               └── <visual_id>/
│                   └── visual.json
```

### Rules

- **Folder name:** `<UseCaseId>.Report` (e.g. `COM-001.Report`).
- **definition/report.json:** Schema `https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json`. Do **not** put `datasetReference` in report.json (Desktop schema disallows additional properties). Dataset binding is in **definition.pbir** only.
- **definition/version.json:** Must exist; `{"version":"1.0"}` or with `$schema`.
- **definition/pages/pages.json:** All page folders in `pageOrder`, and `activePageName` set.
- **Page folders:** Pattern `Page_<UCNoHyphen>_<PageName>`. Each has `page.json` and `visuals/<id>/visual.json`.
- **Report.pbip:** Root ItemShortcut; `artifacts[].report.path = "."`.

## Semantic model layout

```
<Domain>.SemanticModel/
├── SemanticModel.pbip             # artifacts[].dataset.path = "."
├── definition.pbism               # Dataset properties: definitionProperties/1.0.0, version 4.2; required by Desktop Feb 2026+
└── definition/
    ├── model.tmdl
    └── tables/
        ├── *.tmdl
        ├── _Measures.tmdl
        └── _ActionReady_Logic.tmdl
```

Generated domain models under `products/fabric_powerbi/dist/<Domain>.SemanticModel` follow this pattern.

## Delta (incremental) measures

When the pipeline runs for one or a few use cases (e.g. `-UseCase COM-001`), it writes **only** the measure files for those use cases (**delta**), so the shared semantic model is not fully overwritten:

- One file per use case: `definition/tables/_Measures_<UC>.tmdl` (e.g. `_Measures_COM001.tmdl`). Only the use cases in the current run are written; other use cases’ files are left unchanged.
- `model.tmdl` gets `ref table _Measures_<UC>` appended for each written use case (if not already present).

So: run for COM-001 → only `_Measures_COM001.tmdl` is created/updated; COM-002, COM-003, etc. stay as-is. **Migration:** If the folder previously had a single `_Measures.tmdl`, remove that file and remove `ref table _Measures` from `model.tmdl` before using delta, to avoid duplicate tables.

## Validation

- **`products/fabric_powerbi/tooling/check_report_structure.ps1`** validates report folders under dist against this structure.
- **`products/fabric_powerbi/tooling/ensure_pbip_desktop_ready.ps1`** (run from repo root): iterates over dist, auto-adds missing `definition.pbism` (SemanticModel) and `definition.pbir` (Report with definitionProperties schema), then re-runs validation until all checks pass or max iterations. Use after orchestration so Power BI Desktop can open Report + dataset. Example: `.\products\fabric_powerbi\tooling\ensure_pbip_desktop_ready.ps1 -DistRoot products/fabric_powerbi/dist`.
- **`products/fabric_powerbi/tooling/tmdl_render_and_fix.ps1`** (TMDL Script Renderer): runs TMDL syntax and PBIP-readiness checks; on failure writes to `.cursor/tmdl_errors.log`, applies auto-fixes (Spaces→Tabs, remove `description:`), retries; on success after fix appends the solution to `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` (Learning Loop). Called automatically by `pbi_validate_after_impl.ps1`; can be run standalone: `.\products\fabric_powerbi\tooling\tmdl_render_and_fix.ps1`.
- Pipeline: `orchestrate_full_model.ps1` writes reports via `page_scaffold_generator/generate_full_report.py`. Do not rely on the fallback `report_generator.ps1` for report content—it produces a different report.json shape and is not PBIP-compliant.

## Example

A conforming sample report (no datasetReference, design-time only): `showcases/aurora_group/reports/COM-001.Report`.
