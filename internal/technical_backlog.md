# Technical Backlog

**Purpose:** Single place for technical TODOs and stubs that are not covered by [internal/vision/phase2_backlog.md](vision/phase2_backlog.md) (functional topics: 3-30-300, Strategy Pattern). Use this document to find and track code-level open items.

**Tracking:** Work items are tracked in the repo-scope GitHub Project. For migration of these items to Issues, see [internal/project_mgmt/BACKLOG_MIGRATION.md](project_mgmt/BACKLOG_MIGRATION.md).

**Last updated:** 2026-02-19

---

## Power BI MCP / Fabric

| File | Context | Description |
|------|---------|-------------|
| products/fabric_powerbi/orchestrator/table_ops.ps1 | ~line 138 | Builder Engine: TMDL output in PBIP (no MCP call). Optional MCP integration later. |
| products/fabric_powerbi/orchestrator/relationship_ops.ps1 | ~line 199 | Builder Engine: relationships TMDL in PBIP (no MCP call). Optional MCP integration later. |
| products/fabric_powerbi/orchestrator/deploy.ps1 | lines 44, 52, 59, 72 | Fabric Workspace API (GET/POST); Import PBIP/TMDL to semantic model API; Publish report and bind to dataset; Apply RLS / security_user_org mapping via API. Refresh schedule via REST implemented (step 5). |
| products/fabric_powerbi/orchestrator/AUTOMATION_FLOW.md | multiple | TMDL default format strings and display folders; Measure binding in visuals; Action Codes in panel; Fabric REST API; Refresh schedule; security_user_org mapping. |

**Phase 1 done:** Registry as build prerequisite; Domain mode (COM-* Relationships/Hierarchies, one report per use case); Full-Report via `generate_full_report.py` (overview + detail, datasetReference); Quality checks as hard gate; Bracket schema `ux_bindings` optional. **Open:** deploy.ps1 real API; measure/axis binding; Action Panel content; Streamlit Bindings/Actions tabs.

---

## Aurora Models (Operations, Finance)

Open work for Operations and Finance domain models is tracked in **[products/fabric_powerbi/blueprints/README.md](../products/fabric_powerbi/blueprints/README.md) § Next Steps**: complete relationships/measures/display folders, add DAX expressions to KPI Catalog, populate Measure_Dictionary per domain. The in-file comments in `Operations.yaml` and `Finance.yaml` point to that section.

---

## Synthetic Data

| File | Context | Description |
|------|---------|-------------|
| core/data_contracts/sources/synthetic/fabric_nb_generate_backbone_core_v1.py | line 12 | Lakehouse must exist (create first). |
| core/data_contracts/sources/synthetic/fabric_nb_generate_backbone_core_v1.py | lines 79, 116, 154, 189, 219, 266, 304, 357, 365, 375, 478, 483 | Generate date range with Spark; stub blocks; derive from sales + config.inventory (target_dio_range, coverage days); implement join + ratio; Category join + GM% band check; RI dim_* vs facts, margin bands, DIO/CCC bands; ensure Lakehouse and schema exist; map dims/facts to config.lakehouse.tables. |
| core/data_contracts/sources/synthetic/generate_gold_layer.py | line 121 | Optional: add holiday logic for `is_holiday` column. |

---

## Page Scaffold Generator

| File | Context | Description |
|------|---------|-------------|
| products/fabric_powerbi/tooling/page_scaffold_generator/yaml/scanner.py | line 187 | Support for BOM (byte-order mark) within a stream. |
| products/fabric_powerbi/tooling/page_scaffold_generator/yaml/scanner.py | line 761 | Tab handling rules (clarify/sanitize). |
| products/fabric_powerbi/tooling/page_scaffold_generator/yaml/`__init__.py` | line 21 | XXX: "Warnings control" API is deprecated; left in place to avoid breaking callers. No implementation work. |

---

## Intentional placeholders (not implementation TODOs)

These behaviours are by design. They are not open work to "fix"; they require manual follow-up or are fallbacks when input is missing.

| File | Behaviour |
|------|-----------|
| tooling/generation/generate_tmdl_measures.ps1 | Emits `// TODO` and `BLANK()` when no DAX expression is available for a measure. |
| tooling/generation/generate_measures.ps1 | Uses `// TODO: define expression for <kpi_id>` when `dax_expression` is missing. |
| tooling/generation/generate_tmdl_measures_simple.ps1 | Emits `// TODO` placeholder for measures without expression. |
| tooling/maintenance/migrate_brackets_v2.py | Sets `evidence_grain` to `TODO_SET_EVIDENCE_GRAIN` when missing or forbidden (e.g. `transaction_line`). Run `tooling/maintenance/sync_evidence_grain_note_to_factsheet.ps1` and fix grain manually per use case; see core/data_contracts/domains and internal/evidence_grain_audit_results.md. |
| tooling/maintenance/convert_kpi_catalogs.py | Uses default `"TODO - add interpretation."` when interpretation key is missing during conversion. |
