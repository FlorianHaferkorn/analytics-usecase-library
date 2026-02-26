# Known errors and fixes (Builder Engine / Fabric pipeline)

Purpose: Single **knowledge base** for PBI/PBIP errors and their **solutions**. Capture recurring build/validate and Desktop errors so the learning loop can prevent or resolve them. When a new error class is fixed, add an entry in the tables below (Symptom | Cause | Fix) and consider a BPA/TMDL rule or script check to catch it next time.

## Closed-loop (Power BI Desktop + Cursor)

- **Live Desktop errors:** Watcher `watch_pbi.ps1` (repo root) tails `PBIDesktop.log` and appends matching lines to **`.cursor/pbi_errors.log`** (bridge file for Cursor). Run with `.\watch_pbi.ps1` while working in Power BI Desktop.
- **This file is the Wissensdatenbank:** Errors **and** solutions live in the tables below. When the agent (or a human) fixes an error from `.cursor/pbi_errors.log` or from pipeline logs, it must **add a new row** to the appropriate section if this error class is not yet documented (so the solution is stored and reusable).
- **MCP workflow:** When using the Power BI Modeling MCP to diagnose or fix model/report issues, the agent should **read this file first** for known patterns and **update this file** after applying a fix for a new error (add Symptom | Cause | Fix).
- **Automatischer Fix (Daemon):** Wenn gewünscht, läuft im Hintergrund `.\tooling\pbi_auto_fix_daemon.ps1`. Er überwacht `.cursor/pbi_errors.log`; bei neuem Eintrag wird nach Debounce eine LLM-API (Azure OpenAI oder OpenAI) aufgerufen und die zurückgegebene Korrektur (file_edits + optional neue Zeile hier) angewendet. Voraussetzung: `AZURE_OPENAI_*` oder `OPENAI_API_KEY` gesetzt; siehe Skript-Kommentar.
- **Post-Implementation (Agent):** Nach Abschluss einer MCP- oder manuellen Implementierung führt der Agent `.\tooling\pbi_validate_after_impl.ps1` aus, wartet auf das JSON-Ergebnis, behebt bei Fehlern (und trägt neue Lösungen hier ein), und wiederholt bis `success` oder max. Iterationen. Siehe `.cursor/rules/fabric-expert.mdc` (Post-Implementation).

**Error log locations:**

| Source | Path |
|--------|------|
| Pipeline (orchestrator) | `products/fabric_powerbi/orchestrator/last_run_state.json` (`validateErrors`), `products/fabric_powerbi/orchestrator/out/build_errors.json` |
| Quality Checks failures | `internal/reviews/run_all_checks_failures.json` |
| Power BI Desktop (live) | `.cursor/pbi_errors.log` (filled by `watch_pbi.ps1`) |

---

## TMDL / PBIP

| Symptom / message | Cause | Fix |
|------------------|--------|-----|
| TMDL validation failed; rule violation | BPA rule (e.g. description vs /// comment, naming) | Run `validate_tmdl.ps1 -AutoFix` or fix TMDL per `tooling/linters/powerbi/bpa-rules-tmdl.json`. |
| Missing .pbip file; PBIP structure invalid | Report or model folder not PBIP-compliant | Ensure folder has `.pbip` and `definition/` (and for reports `definition/report.json`, `datasetReference`). Use page_scaffold_generator / Fabric output layout. |
| definition.pbir / report.json missing $schema | Generator or template omitted schema | Add `"$schema"` to the JSON per Power BI PBIP schema. |
| check_tmdl_syntax: model.tmdl tmdl.indent.tabs_only (Phase 6 Fabric checks fail) | model.tmdl written with spaces for indentation | TMDL requires TABs only. In orchestrate_full_model.ps1 use `` `t `` for model content (culture, defaultPowerBIDataSourceVersion). Fix existing dist: replace leading spaces with tab in definition/model.tmdl. |
| TMDL Indentation / invalid indent at column (e.g. "column Promo Flag", line 24) | Column or object names that contain spaces are parsed as multiple tokens and break indentation. | Quote identifiers that contain spaces: use `column 'Promo Flag'` (single quotes). Fix all such columns in the .tmdl file. **Generator:** `products/fabric_powerbi/orchestrator/table_ops.ps1` outputs `column 'Name'` when `$col.name -match ' '` so new tables get correct TMDL. See learn.microsoft.com TMDL overview. |
| Object "Action_C-M2.1_Text" (Measure) could not be added because an object of the same name already exists | Action-Code-Measures were emitted in both _Measures.tmdl and_ActionReady_Logic.tmdl; Power BI allows only one measure per name. | When using TargetTablesDir (Aurora shared model), action measures live only in _Measures (displayFolder 9_ActionReady_Logic)._ActionReady_Logic.tmdl must be **shell only** (table + partition + column, no measures). Generator: `generate_tmdl_measures.ps1` calls `Build-ActionReadyLogicTable -ShellOnly` when `$resolvedTablesDir` is set. |
| TMDL Indentation at _ActionReady_Logic, line 6 "isHidden" | Table-level properties had mixed indentation (e.g. lineageTag with two tabs, isHidden with one), or extra lineageTag was inserted with wrong indent. | Use **one tab** for all direct table properties (e.g. `isHidden`). Remove or fix any `lineageTag` so it also has exactly one tab. Do not add lineageTag to _ActionReady_Logic unless the generator does; regenerating the file with the script restores correct structure. |
| TMDL Indentation at _Measures, line 5 "partition_Measures = m" | Table-level lineageTag was inserted with **two tabs** (e.g. by validate_tmdl.ps1 -AutoFix); parser then treats the next line (partition) as invalid. | Use **one tab** for all direct table children (partition, column, table-level props). Remove wrongly indented lineageTag or fix AutoFix: `validate_tmdl.ps1` Add-LineageTag must use one tab for table, indent+tab for column. Regenerating _Measures.tmdl (generate_tmdl_measures.ps1) produces no lineageTag in header; avoid re-running AutoFix that adds two-tab lineageTag. |
| Measures don't work; formatString/displayFolder "wrong" or DAX contains ``` | TMDL measure: (1) Code fences (```) in DAX are not valid; (2) multiline DAX can cause indent ambiguity. | **Generator:** One line per measure: `measure 'Name' = <DAX>` (DAX joined with space). **formatString/displayFolder must be at t2** (one tab deeper than measure); Desktop Feb 2026 reports "ungültiger Einzug" (invalid indentation) at formatString if at t1. In `Build-ActionTextMeasureBlock` use t2 for isHidden, displayFolder, annotations. Do not use ```. Regenerate with `generate_tmdl_measures.ps1 -OverwriteExisting`. |
| Expected '$schema' in Report.pbip to follow pattern … pbip/pbipProperties/1.[0-9]+.[0-9]+/schema.json (Power BI Desktop) | .pbip used old `fabric/gitIntegration/itemShortcut/1.0.0/schema.json` | Use `fabric/pbip/pbipProperties/1.0.0/schema.json` in all .pbip files. Report: `products/fabric_powerbi/tooling/page_scaffold_generator/pbip_writer.py` (PBIP_SCHEMA). SemanticModel.pbip in orchestrate: add same `$schema` if Desktop validates it. |
| ReportDefinition: Required artifact is missing … definition.pbir (Power BI Desktop Feb 2026+) | Desktop expects `definition.pbir` at report root; we only had `definition/report.json`. | Generator writes `definition.pbir` with **definitionProperties** schema (version + datasetReference), not report definition. `pbip_writer._write_definition_pbir()`. Doc: `PBIP_REPORT_STRUCTURE.md`. |
| Expected '$schema' in definition.pbir to follow definitionProperties/1.x or 2.x (UnrecognizedSchemaVersion) | We wrote definition.pbir with definition/report/3.0.0 schema; Desktop expects definitionProperties. | Use `definitionProperties/2.0.0/schema.json` and payload: version "4.0", datasetReference.byPath. See samples in `showcases/sample_pbip_report/` and `pbip_writer._write_definition_pbir()`. |
| DatasetDefinition: Required artifact is missing … definition.pbism (Power BI Desktop Feb 2026+) | Desktop expects `definition.pbism` at semantic model root; we only had SemanticModel.pbip and definition/ (TMDL). | Write `definition.pbism` with schema `semanticModel/definitionProperties/1.0.0`, version "4.2", settings {}. Orchestrator does this in the same loop as SemanticModel.pbip. Doc: `PBIP_REPORT_STRUCTURE.md`. |
| Can't resolve schema '1.0.0' in version.json (Power BI Desktop Feb 2026+) | Desktop expects version.json to use **versionMetadata** schema, not **version**. Wrong schema or version value. | Use `$schema`: `fabric/item/report/definition/versionMetadata/1.0.0/schema.json` and `"version": "2.0.0"`. Generator: `pbip_writer.write_version_json()`. Sample: `showcases/sample_pbip_report/.../definition/version.json`. |
| Property 'datasetReference' has not been defined … report.json (schema does not allow additional properties) | We put datasetReference in definition/report.json; the report definition schema does not allow it. | Remove datasetReference from report.json. Dataset binding belongs only in **definition.pbir**. Generator: `pbip_writer.write_report_json()` must not add datasetReference to report_data. Doc: `PBIP_REPORT_STRUCTURE.md`. |
| Semantic model / Report „öffnet mit Fehlern“ oder Schema-Fehler beim Öffnen in Desktop | Fehlendes `$schema` in .pbip (z. B. SemanticModel.pbip nur mit version/artifacts), oder fehlende definition.pbism/pbir. | **Sofort:** Von Repo-Root `.\products\fabric_powerbi\tooling\ensure_pbip_desktop_ready.ps1` ausführen – ergänzt fehlende definition.pbism/pbir und `$schema` in allen .pbip. **Dauerhaft:** Orchestrator schreibt SemanticModel.pbip mit `$schema`; Post-Implementation-Validierung (`pbi_validate_after_impl.ps1`) ruft ensure_pbip_desktop_ready vor den Fabric-Checks auf. |
| TMDL-Validierung schlägt fehl (Syntax/Readiness) | Spaces statt Tabs, description:-Property, oder PBIP-Readiness-Regeln. | **TMDL Script Renderer:** `.\products\fabric_powerbi\tooling\tmdl_render_and_fix.ps1` ausführen. Er prüft TMDL, schreibt Fehler nach `.cursor/tmdl_errors.log`, wendet Auto-Fixes an (Spaces→Tabs, description entfernen) und trägt nach erfolgreichem Fix die Lösung in diese Tabelle ein (Learning Loop). Optional in Pipeline/Validierung einbinden. |
| TMDL "ungültiger Einzug" bei formatString/displayFolder (Desktop Feb 2026, Zeile 21 _Measures) | Measure-Properties (formatString, displayFolder) mit nur **einem Tab** (t1) – Desktop erwartet **zwei Tabs** (t2), also eine Ebene tiefer als die measure-Zeile. | **Generator:** In `Build-MeasureBlock` und `Build-ActionTextMeasureBlock` alle Measure-Properties (formatString, displayFolder, isHidden, annotations) mit **t2** ausgeben. Dann `generate_tmdl_measures.ps1 -OverwriteExisting` und **vor Test** `.\products\fabric_powerbi\tooling\run_fabric_checks.ps1` bzw. `tmdl_render_and_fix.ps1` ausführen. |
| Daten-Spalten (integer, decimal etc.) sollen nicht automatisch zusammengefasst werden | Power BI kann numerische Spalten standardmäßig summieren; für konsistente Berichte soll keine implizite Aggregation erfolgen. | **Standard:** Alle Daten-Spalten mit `summarizeBy: none`. **CreateFromContract** (table_ops.ps1) schreibt bei Tabellenerstellung bereits `summarizeBy: none` pro Spalte. **PatchAddSummarizeByNone** ergänzt fehlende `summarizeBy: none` nach `sourceColumn` (wird im Orchestrator ausgeführt). |

---

## DAX / measures

| Symptom / message | Cause | Fix |
|------------------|--------|-----|
| DAX syntax error; invalid expression | Typo, unsupported function, or := in expression | Fix DAX (no `:=`); ensure KPI catalog / Measure_Dictionary DAX is valid. Run `check_dax_best_practices.ps1`. |
| Measure not found; KPI ID missing in catalog | Use case or action code references non-existent KPI | Add KPI to `core/kpi_catalog/` or fix reference in factsheet/bracket. Run `check_factsheet_vs_kpi.ps1` and `check_action_codes_vs_kpi.ps1`. |
| "Der Wert für die Spalte 'Cost of Goods Sold Amount' kann nicht ermittelt werden" (or similar base measure) | A measure referenced in DAX (e.g. [Cost of Goods Sold Amount]) does not exist; often a **base** measure (SUM of fact column) not listed as KPI. | Add the base measure as a KPI in `core/kpi_catalog/` (e.g. `cost.cogs.amount` with dax_expression `SUM ( fact_sales[Cost of Goods Sold Amount] )`) and add its kpi_id to the use case's `influencing_kpi_ids` in `UseCase_Bracket.yaml`. Then regenerate measures. |

---

## datasetReference

| Symptom / message | Cause | Fix |
|------------------|--------|-----|
| datasetReference missing or empty | Report JSON has no or invalid datasetReference | Set `datasetReference.byPath` (e.g. `..\Commercial.SemanticModel`) in report definition. Pass `--dataset-reference` to generate_full_report.py. |
| Report cannot connect to dataset | Path wrong or model not built | Ensure domain model exists under dist and path is relative from report folder (e.g. `..\<Domain>.SemanticModel`). |
| Tables empty; no data in report | Partitions use Blank #table when orchestrator was run **without** -UseAuroraData. | Run the orchestrator with **-UseAuroraData** so partition sources are set to GoldDataPath (Aurora gold Parquet). Example: `.\products\fabric_powerbi\orchestrator\orchestrate_full_model.ps1 -UseCase COM-001 -UseAuroraData`. See orchestrator README. Alternativ nur Partitionen patchen: `table_ops.ps1 -Operation PatchPartitionSourceToGoldDataPath -DefinitionPath products\fabric_powerbi\dist\Commercial.SemanticModel\definition`. |
| Semantisches Modell „unvollständig“; nicht alle Tabellen sichtbar | `model.tmdl` enthält nicht für jede Tabelle in `definition/tables/` ein `ref table <Name>`. | Orchestrator ab Build: Schritt „Sync model.tmdl refs“ fügt fehlende `ref table X` für alle .tmdl in tables/ ein. Manuell: In `definition/model.tmdl` pro Tabelle eine Zeile `ref table <Tabellenname>` ergänzen (z. B. _Measures, fact_sales, dim_date, dim_org, dim_product, dim_customer, _ActionReady_Logic). |

---

## pbi-tools compile

| Symptom / message | Cause | Fix |
|------------------|--------|-----|
| pbi-tools not found | pbi-tools not installed | Install e.g. `winget install pbi-tools`. Pipeline continues without compile (warning only). |
| compile failed; TMDL parse error | Invalid TMDL in folder | Fix TMDL syntax and run `run_fabric_checks.ps1` and validate_tmdl first. |
| compile failed; missing artifact | PBIP folder incomplete | Ensure .pbip, definition/, and required JSON files exist. Run `validate_pbip.ps1 -Root <folder>`. |

---

## run_all_checks / Quality Checks

| Symptom / message | Cause | Fix |
|------------------|--------|-----|
| Invalid YAML: core\\templates\\page_templates\\governance\\Color_Semantics_Formatting.yaml (and Layout_Grid_System, Visual_to_Slot_Mapping) | Those files have extension `.yaml` but content is **Markdown** (headings, tables, code blocks); YAML parser fails. | They are governance **docs**, not config. `tooling/validation/check_yaml_format.ps1` skips any `.yaml`/`.yml` file whose path contains a **governance** directory (e.g. `.../page_templates/governance/...`). Do not rename to .md unless all references are updated. |
| Das angegebene Pfadformat wird nicht unterstützt | Transcript or path with unsupported format (e.g. mixed slashes) | run_all_checks normalizes transcript path; ensure repo root has no invalid chars. If it persists, check which script receives the path. |
| Prompt for UseCaseId / TmdlPath | Child script invoked without explicit params | run_all_checks now passes all params and uses `$null \| & script` so no pipeline input is consumed. Ensure you run from repo root. |
| Run Quality Checks FAIL (orchestrate) | One or more checks failed | Inspect `internal/reviews/run_all_checks_failures.json` for failed check names and errors; fix per table in this doc; re-run. |
| check_factsheet_layout: Layout mismatches | Business factsheet headings != template | Template is Lean 2.0: `core/usecases/templates/usecase_factsheet_business.md`. Align factsheet sections to that template or update template if standard changed. |

---

## run_fabric_checks

| Symptom / message | Cause | Fix |
|------------------|--------|-----|
| check_measures_vs_kpi failed | Measure in TMDL not in KPI catalog or mismatch | Align measures with `core/kpi_catalog/` and Measure_Dictionary; fix displayFolder / KPI IDs. |
| check_tmdl_pbip_readiness failed | TMDL not PBIP-ready | Fix TMDL structure per check output; run TMDL validation and BPA. |

---

## Scripts / Generator (PowerShell, Python)

| Symptom / message | Cause | Fix |
|------------------|--------|-----|
| Unerwartetes Token "```" in Ausdruck (generate_tmdl_measures.ps1, Zeile ~814) | In PowerShell inside **double** quotes, backtick (`` ` ``) escapes the next character; `` "```" `` is parsed incorrectly. | Use **single** quotes for literal backticks: `` $lines += ($t2 + '```') ``. No other change; the script was later updated to not output ``` at all (see TMDL measure row above). |

---

## Updating this list

When you fix a new error from `last_run_state.json` or `build_errors.json`:

1. Add a row above under the right section (or add a section).
2. If the error can be caught by an existing or new rule, add/update a check in `run_fabric_checks.ps1` or validation scripts so the next run fails fast with a clear message.
