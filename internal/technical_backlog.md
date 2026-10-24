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
| core/usecases/core/COM-001_Sales_Performance | `slicer_field` ohne Wirkung | 24.10.2026: Kreuztabelle Region > Country > Store umgesetzt, `slicer_field: dim_product.Category` laut Audit. Kein Generator rendert es für COM-001: der Prototyp setzt Slicer_Pane fest auf den Monat und Slicer_Entity fest auf OrgName, der Superversion-Weg liest `slicer_field` nur für einen belegten Slicer_Pane-Slot (COM-001-Golden unverändert). Die Kategorie fehlt damit im Report. **Erledigt 24.10.2026:** der Prototyp liest `slicer_field` für Slicer_Entity (Fallback OrgName), außer das Feld steht schon in `row_fields` (XD-004: `domain`, bleibt OrgName). Wirkung, gemessen am Generator-Diff gegen dist (nur Slicer_Entity geändert): COM-001 Category, FIN-002 Entity, OPS-001 AssetName; XD-004 byte-gleich. Validator je 0 Fehler, 3 Warnungen. Der Superversion-Weg (Slicer_Pane) bleibt unverändert. |
| products/fabric/powerbi/dist/*.SemanticModel | fehlende Dimensionen | 24.10.2026: `site`/`scope` (ESG-001), `cost_center` (FIN-003), `role` (HR-001) und `supplier` (SCM-004) lassen sich nicht auflösen. dim_role und dim_employee_segment liegen im Gold, aber in keinem Modell. Erledigt 24.10.2026: `rep` (COM-005), dim_salesrep, dim_sales_stage, fact_pipeline und fact_sales_target per `tooling/codegen/model_alignment.py` im Commercial-Modell; dim_cost_center und fact_opex_costcenter per demselben Codemod im Finance-Modell (Gold-FK-Treffer CostCenterKey/OrgKey/DateKey je 100 %, 94.560 Zeilen). Offen für FIN-003: das Token `cost_center` bleibt bewusst ohne Auflösung, weil alle fünf Evidenz-KPIs auf fact_finance bzw. fact_sales rechnen und eine Kostenstellen-Zeile jeden Wert nur wiederholen würde. Weg: KPI-FIN-014 (OpEx vs Plan %) auf fact_opex_costcenter umziehen; die Summen stimmen je Org×Monat überein (32.040 Zellen, max. 0,01 EUR, pandas). **Erledigt 24.10.2026 (Freigabe Florian Haferkorn):** KPI-FIN-014 rechnet auf fact_opex_costcenter, `cost_center` löst zu dim_cost_center.'Cost Center' auf. **Weiter offen:** der FIN-003-Report ist nicht erzeugt. dim_cost_center hängt nur an fact_opex_costcenter; KPI-FIN-018/021/020 (fact_finance) und KPI-COM-013 (fact_sales) ignorieren den Kostenstellenfilter, eine Zeile Entity × Kostenstelle (534 × 6, Gold) wiederholte also vier von fünf Werten (hergeleitet aus den Beziehungen, nicht im Tenant gemessen). Wege: (a) Evidenz auf kostenstellenfähige Spalten schneiden (KPI-FIN-014 plus OpEx-Beträge, Sortierung nach KPI-FIN-014); (b) Entity-Körnung mit allen fünf KPIs, Kostenstelle als Drillthrough; (c) weitere KPIs auf eine Kostenstellen-Allokation umziehen. Bracket-Entscheidung, braucht Freigabe. **Entschieden 24.10.2026 (Florian Haferkorn): Weg (b).** Evidenz Entity-Körnung mit allen fünf KPIs, Sortierung nach KPI-FIN-021; Main_2 rankt nur KPI-FIN-014 (vorher mit KPI-COM-013 auf einer Achse, ONE_MESSAGE_PER_CHART). Report erzeugt (powerbi-report-author 0 Fehler, 3 Warnungen), aber **nicht ausgeliefert**: `test_no_broken_measure_bindings` meldet 9 Bindungen ins Leere. Dem Finance-Modell fehlen die Measures für KPI-FIN-018 (EBITDA Margin), KPI-FIN-020 (EBITDA), KPI-FIN-021 (EBITDA Margin vs Plan) und die Spalten `Plan EBITDA Amount`/`Plan Net Sales Amount` (im Gold vorhanden, fact_finance, 5 aktive Dateien, pyarrow); KPI-COM-013 und KPI-COM-009 rechnen laut Katalog auf fact_sales, das das Finance-Modell nicht führt. **Offen:** (1) Spalten per `model_alignment.py` + drei FIN-Measures, (2) Entscheidung zu KPI-COM-013/COM-009 im Finance-Report (fact_sales ins Finance-Modell oder KPIs tauschen), (3) Kostenstellen-Drillthrough. **Erledigt 24.10.2026:** (1) `model_alignment.py` legt `Plan Net Sales Amount`/`Plan EBITDA Amount` (fact_finance) und die Measures EBITDA, EBITDA Margin, EBITDA Margin vs Plan an; (2) Entscheidung Florian Haferkorn: tauschen. KPI-COM-013 weicht KPI-FIN-016 (COGS % of Sales, fact_finance); KPI-COM-009 bleibt nur Treiber in der Bracket-Formel (supporting). Report ausgeliefert (powerbi-report-author 0 Fehler, 3 Warnungen; Bindungstests grün). Gold, pandas, fact_finance 32.040 Zeilen: EBITDA 1.755.045.627,41, Marge 12,17 %, Plan 13,56 %, Abweichung −1,39 pp, COGS-Quote 61,01 %; Gleichheit mit der DAX-Quote der Summen hergeleitet, nicht im Tenant gemessen. **Weiter offen (3) Kostenstellen-Drillthrough, Architekturentscheidung:** die dist-Reports erzeugt der als DEPRECATED markierte Prototyp-Renderer; er kennt nur die Detailseite als Drillthrough-Ziel (ohne Drillthrough-Filter, Parameter, Zurück-Button; daher die 3 Validator-Warnungen in jedem Report). Der offizielle Emitter `tooling/superversion/targets/pbir.py` führt `drillthrough_fields` im Vertrag, emittiert es aber nicht, und speist die dist-Reports nicht. Eine dritte Seite im Prototyp wäre ein Nebeneinander zum offiziellen Weg. Wege: (a) `targets/pbir.py` um Drillthrough-Seiten erweitern und FIN-003 als ersten Report über den offiziellen Weg nach dist bringen; (b) Prototyp erweitern (widerspricht I-3.3). Empfehlung (a), braucht Freigabe. **Teil von Weg (a) erledigt 24.10.2026:** `targets/pbir.py` emittiert `drillthrough_fields` als Drillthrough-Seite (`type`/`pageBinding` Drillthrough mit Parametern, je Feld ein Seitenfilter `howCreated: Drillthrough`, Zurück-Button `actionButton` mit `visualLink` Back); das Bracket-Schema kennt `ux_layout_rules.page_3_drillthrough`, `from_aluca` setzt daraus die Seite, FIN-003 deklariert sie (Feld `dim_org.OrgName`, Evidenz `dim_cost_center.Cost Center` + KPI-FIN-014). Gemessen mit powerbi-report-author 0.5.0 `validate --no-schema` am Emitter-Output: FIN-003 0 Fehler, 0 Warnungen (vorher dist-Report 0 Fehler, 3 Drillthrough-Warnungen); zweite Messung jsonschema gegen die gecachten Microsoft-Schemas (page 2.1.0, visualContainer 2.9.0): 11 Dateien, 0 Fehler. Tests in `tooling/superversion/tests/test_pbir_target.py`. **Weiter offen:** FIN-003 nach dist über den offiziellen Weg (die dist-Reports erzeugt weiter der Prototyp, ihre 3 Warnungen bleiben); im offiziellen Output trägt FIN-003 noch drei HITL-Lücken (Main_1/Main_2 ohne Category, Detail_Matrix `entity` unqualifiziert) — dort fehlt also noch das Quell-Visual mit `dim_org.OrgName`, aus dem der Drillthrough startet. Für ESG-001, HR-001 und SCM-004 bindet kein Modell (`domain: Supply Chain` ergibt kein SupplyChain.SemanticModel). |
| core/usecases/core/XD-001_Service_Level_Performance | `top_n` | 24.10.2026 (ADR-0027): nachgemessen 200 Zeilen (Org × Channel × Queue × IssueType × Severity, fact_support_cases, Gold, pandas), daher keine Ausnahme. Das Top-20 liegt auf der letzten Dimensionsspalte Severity (3 Werte) und filtert nichts. **Erledigt 24.10.2026:** weder Spaltenfolge noch Top-N-Feld helfen (je Spalte höchstens 10 Werte, eine Kreuzklassifikation begrenzt kein Einzelfeld-Top-N). Körnung auf die Entscheidungsfrage geschnitten: Channel × Queue × IssueType, 20 Zeilen, `kleine_koernung`; Org gestrichen, Severity hängt 1:1 an IssueType. Nachgezählt per `check_evidence_sort.py --gold`. |
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
