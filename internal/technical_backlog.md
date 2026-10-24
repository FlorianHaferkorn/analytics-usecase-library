# Technical Backlog

**Purpose:** Single place for technical TODOs and stubs that are not covered by [internal/vision/phase2_backlog.md](vision/phase2_backlog.md) (functional topics: 3-30-300, Strategy Pattern). Use this document to find and track code-level open items.

**Tracking:** Work items are tracked in the repo-scope GitHub Project and can be converted to issues directly from this list.

**Last updated:** 2026-06-17

---

## Un-wired tooling (wire-or-remove)

These scripts are functional but referenced by no workflow, runner, hook, README, AGENTS.md, or CLAUDE.md. Decide per item: wire into a gate, or remove. (Surfaced by the 2026-06-17 hygiene audit; a third such script, `tooling/scripts/check_brackets_schema.py`, was removed in the same pass as fully superseded by the pytest schema suite.)

| File | Size | Note |
|------|------|------|
| `tooling/hooks/pre_push_gate.py` | small | Docstring claims a PreToolUse/pre-push hook, but `.claude/settings.json` defines no such hook (only PostToolUse bash hooks). Wire into pre-commit/settings, or remove. |
| `tooling/validation/check_page_dod.py` | 442 lines (CLI w/ `__main__`) | Page Definition-of-Done checker; only self-references, not in any gate/runner/README. Wire into a gate, or document as a manual tool. |

---

## Power BI MCP / Fabric

| File | Context | Description |
|------|---------|-------------|
| products/fabric/powerbi/orchestrator/table_ops.ps1 | ~line 138 | Builder Engine: TMDL output in PBIP (no MCP call). Optional MCP integration later. |
| products/fabric/powerbi/orchestrator/relationship_ops.ps1 | ~line 199 | Builder Engine: relationships TMDL in PBIP (no MCP call). Optional MCP integration later. |
| products/fabric/powerbi/orchestrator/deploy.ps1 | lines 44, 52, 59, 72 | Fabric Workspace API (GET/POST); Import PBIP/TMDL to semantic model API; Publish report and bind to dataset; Apply RLS / security_user_org mapping via API. Refresh schedule via REST implemented (step 5). |
| products/fabric/powerbi/orchestrator/AUTOMATION_FLOW.md | multiple | TMDL default format strings and display folders; Measure binding in visuals; Action Codes in panel; Fabric REST API; Refresh schedule; security_user_org mapping. |

**Phase 1 done:** Registry as build prerequisite; Domain mode (COM-* Relationships/Hierarchies, one report per use case); Full-Report via `generate_full_report.py` (overview + detail, datasetReference); Quality checks as hard gate; Bracket schema `ux_bindings` optional. **Open:** deploy.ps1 real API; measure/axis binding; Action Panel content; Streamlit Bindings/Actions tabs.

---

## Aurora Models (Operations, Finance)

Open work for Operations and Finance domain models is tracked in **[products/fabric/powerbi/blueprints/README.md](../products/fabric/powerbi/blueprints/README.md) § Next Steps**: complete relationships/measures/display folders, populate Measure_Dictionary per domain. The in-file comments in `Operations.yaml` and `Finance.yaml` point to that section.

> **Note (2026-03-29):** DAX expressions have been removed from the KPI Catalog (core is tool-agnostic). DAX now lives exclusively in the Fabric overlay: `products/fabric/powerbi/specs/fabric_measure_overlay.yaml`.
>
> **Nachtrag (2026-08-05):** Das Overlay ist entfallen. Der Katalog traegt die Rechenvorschrift
> wieder — aber als werkzeugneutrale Grammatik (`technical.calculation`), nicht als DAX. Damit
> gilt beides: der Kern bleibt tool-agnostisch, und es gibt nur eine Quelle. Die Trennung lag
> nie zwischen Katalog und Overlay, sondern zwischen Bedeutung und Syntax.

---

## Synthetic Data

**Status:** ✅ Backbone Core v1 generator fully implemented (2026-03-28). All 14 dimension and fact generators, QA checks, and Lakehouse write logic now have complete PySpark implementations. Only the Lakehouse must exist before running.

| File | Context | Description |
|------|---------|-------------|
| core/data_contracts/sources/synthetic/fabric_nb_generate_backbone_core_v1.py | line 13 | Lakehouse must exist before running (Fabric prerequisite). |
| core/data_contracts/sources/synthetic/generate_gold_layer.py | line 121 | Optional: add holiday logic for `is_holiday` column. |

---

## Page Scaffold Generator

| File | Context | Description |
|------|---------|-------------|
| products/fabric/powerbi/tooling/page_scaffold_generator/yaml/scanner.py | line 187 | Support for BOM (byte-order mark) within a stream. |
| products/fabric/powerbi/tooling/page_scaffold_generator/yaml/scanner.py | line 761 | Tab handling rules (clarify/sanitize). |
| products/fabric/powerbi/tooling/page_scaffold_generator/yaml/`__init__.py` | line 21 | XXX: "Warnings control" API is deprecated; left in place to avoid breaking callers. No implementation work. |
| products/fabric/powerbi/tooling/page_scaffold_generator/config_loader.py | `EVIDENCE_DIM_TOKENS`, `_pick_column` | 24.10.2026 (Matrix-Sichtung, `internal/evidence_grain_audit_results.md`): Evidence-Aliase treffen die falsche Tabelle: `segment` (HR-001) → dim_customer, `category` (SCM-004) → dim_product statt dim_category, `channel` (XD-001/002) → dim_org statt dim_case_queue, `period` (XD-003) → dim_date.Date (Tageskörnung). **Erledigt 24.10.2026:** die vier Brackets nennen die Spalte qualifiziert (`dim_employee_segment.Segment`, `dim_category.Category`, `dim_case_queue.Channel`), `period` ist aus XD-003 gestrichen; `_table_column` bricht bei einer unbekannten `dim_`/`fact_`-Tabelle mit ihrem Namen ab, statt sie als Measure zu lesen. Tests in `tests/test_rollout_2026_09_23.py`. Die Alias-Tabelle selbst bleibt unverändert (andere Use Cases lösen über sie richtig auf). |
| products/fabric/powerbi/dist/*.SemanticModel | fehlende Dimensionen | 24.10.2026: `site`/`scope` (ESG-001), `cost_center` (FIN-003), `role` (HR-001) und `supplier` (SCM-004) lassen sich nicht auflösen. dim_role und dim_employee_segment liegen im Gold, aber in keinem Modell. Erledigt 24.10.2026: `rep` (COM-005), dim_salesrep, dim_sales_stage, fact_pipeline und fact_sales_target per `tooling/codegen/model_alignment.py` im Commercial-Modell; dim_cost_center und fact_opex_costcenter per demselben Codemod im Finance-Modell (Gold-FK-Treffer CostCenterKey/OrgKey/DateKey je 100 %, 94.560 Zeilen). Offen für FIN-003: das Token `cost_center` bleibt bewusst ohne Auflösung, weil alle fünf Evidenz-KPIs auf fact_finance bzw. fact_sales rechnen und eine Kostenstellen-Zeile jeden Wert nur wiederholen würde. Weg: KPI-FIN-014 (OpEx vs Plan %) auf fact_opex_costcenter umziehen; die Summen stimmen je Org×Monat überein (32.040 Zellen, max. 0,01 EUR, pandas). Katalog-Lineage-Änderung, braucht Freigabe. Für ESG-001, HR-001 und SCM-004 bindet kein Modell (`domain: Supply Chain` ergibt kein SupplyChain.SemanticModel). |
| showcases/aurora_group/data/gold/facts | gemischte Org-Ebenen | 24.10.2026: fact_support_cases, fact_workforce_management, fact_accounts_receivable und fact_fulfillment buchen auf Group-, Region-, Country- und Store-Zeilen zugleich (OrgType). Zwischensummen über dim_org zählen doppelt; das sperrt eine Org-Matrix in diesen Domänen. |

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

---

## Completed Items (2026-03-29)

| Item | Description |
|------|-------------|
| KPI Catalog: DAX removal | Removed `dax_expression` (110), `formatString` (113) from core KPI Catalog. Renamed `dax_name` → `measure_name`. DAX lives in Fabric overlay. |
| KPI Catalog: YAML fixes | Fixed 28+41 malformed `domain_tag` entries (dangling list items). Fixed self-referential dep on `KPI-SVC-013`. |
| KPI Catalog: completeness scores | Updated 17 entries from 0.6 → 1.0 (incomplete DAX no longer penalizes score). |
| KPI Catalog Schema | Updated `kpi_catalog_SCHEMA.md`: removed `dax_expression`/`formatString`, renamed `dax_name` → `measure_name`. |
| Measure Dictionaries: logical expressions | Completed tool-agnostic pseudocode for 223 placeholder measures (was "Fabric: see overlay / TMDL"). Added `aggregation_method` to all. |
| Measure Dictionaries: display_folder | Added missing `display_folder` values to Liquidity domain measures. |
| Data Contracts: SCD types | Added `scd_type: 1\|2` to all dimension definitions across 13 domain contracts. |
| Data Contracts: cardinality | Added `cardinality: many-to-one` to fact→dim foreign key columns. |
| Data Contracts: grain compatibility | Created `GRAIN_COMPATIBILITY.md` documenting safe joins between fact grains. |
| Business Factsheets: KPI summaries | Embedded KPI & Action Code overview tables in all 15 factsheets (from UseCase_Bracket.yaml). |
| Downstream tooling | Updated `build_ir.py`, `validate_kpi_catalog.ps1`, `convert_kpi_catalogs.py`, `audit_missing_dax.ps1` for `measure_name` field. |
| pytest config | Fixed conftest.py collision via `norecursedirs` in pyproject.toml. |
