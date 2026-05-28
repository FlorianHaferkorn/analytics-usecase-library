# Known errors and fixes (Builder Engine / Fabric pipeline)

Purpose: Single **knowledge base** for PBI/PBIP errors and their **solutions**. Capture recurring build/validate and Desktop errors so the learning loop can prevent or resolve them. When a new error class is fixed, add an entry in the tables below (Symptom | Cause | Fix) and consider a BPA/TMDL rule or script check to catch it next time.

**Pflicht (Agent und Mensch):** Nach **jedem** behobenen Fehler (aus Pipeline, Desktop, Nutzerbericht oder eigener Analyse) **muss** eine neue Zeile in die passende Tabelle unten eingetragen werden, sofern diese Fehlerklasse noch nicht dokumentiert ist. So werden Lösungen wiederverwendbar und derselbe Fehler nicht mehrfach gemacht. Bei Generatoren: Fix im Generator umsetzen **und** hier dokumentieren.

## Closed-loop (Power BI Desktop + Cursor)

- **Live Desktop errors:** Errors from Power BI Desktop appear in `.cursor/pbi_errors.log` (bridge file for Cursor). Use `fab` CLI or the MCP `execute_dax` tool for live DAX validation instead of the removed `watch_pbi.ps1` watcher.
- **This file is the Wissensdatenbank:** Errors **and** solutions live in the tables below. When the agent (or a human) fixes an error from `.cursor/pbi_errors.log` or from pipeline logs, it must **add a new row** to the appropriate section if this error class is not yet documented (so the solution is stored and reusable).
- **MCP workflow:** When using the Power BI Modeling MCP to diagnose or fix model/report issues, the agent should **read this file first** for known patterns and **update this file** after applying a fix for a new error (add Symptom | Cause | Fix).
- **Automatischer Fix (Daemon):** Wenn gewünscht, läuft im Hintergrund `.\tooling\pbi_auto_fix_daemon.ps1`. Er überwacht `.cursor/pbi_errors.log`; bei neuem Eintrag wird nach Debounce eine LLM-API (Azure OpenAI oder OpenAI) aufgerufen und die zurückgegebene Korrektur (file_edits + optional neue Zeile hier) angewendet. Voraussetzung: `AZURE_OPENAI_*` oder `OPENAI_API_KEY` gesetzt; siehe Skript-Kommentar.
- **Post-Implementation (Agent):** Nach Abschluss einer MCP- oder manuellen Implementierung führt der Agent `.\tooling\pbi_validate_after_impl.ps1` aus, wartet auf das JSON-Ergebnis, behebt bei Fehlern (und trägt neue Lösungen hier ein), und wiederholt bis `success` oder max. Iterationen. Siehe `.cursor/rules/fabric-expert.mdc` (Post-Implementation).

**Error log locations:**

| Source | Path |
|--------|------|
| Pipeline (orchestrator) | `products/fabric_powerbi/orchestrator/last_run_state.json` (`validateErrors`), `products/fabric_powerbi/orchestrator/out/build_errors.json` |
| Quality Checks failures | `internal/reviews/run_all_checks_failures.json` |
| Power BI Desktop (live) | `.cursor/pbi_errors.log` |

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
| TMDL Indentation at _ActionReady_Logic, line 17 `lineageTag` | A column property under `column _Placeholder` was indented at the same level as the column object instead of one level deeper, so Desktop rejected the file although simple tab-only checks passed. | Under a column object, every property including `lineageTag` must be indented with **two tabs**. Fix the file and keep a structural syntax check that enforces child properties to be deeper than their parent object. |
| TMDL Indentation at _Measures, line 5 "partition_Measures = m" | Table-level lineageTag was inserted with **two tabs** (e.g. by validate_tmdl.ps1 -AutoFix); parser then treats the next line (partition) as invalid. | Use **one tab** for all direct table children (partition, column, table-level props). Remove wrongly indented lineageTag or fix AutoFix: `validate_tmdl.ps1` Add-LineageTag must use one tab for table, indent+tab for column. Regenerating _Measures.tmdl (generate_tmdl_measures.ps1) produces no lineageTag in header; avoid re-running AutoFix that adds two-tab lineageTag. |
| Measures don't work; formatString/displayFolder "wrong" or DAX contains ``` | TMDL measure: (1) Code fences (```) in DAX are not valid; (2) multiline DAX can cause indent ambiguity. | **Generator:** One line per measure: `measure 'Name' = <DAX>` (DAX joined with space). **formatString/displayFolder must be at t2** (one tab deeper than measure); Desktop Feb 2026 reports "ungültiger Einzug" (invalid indentation) at formatString if at t1. In `Build-ActionTextMeasureBlock` use t2 for isHidden, displayFolder, annotations. Do not use ```. Regenerate with `generate_tmdl_measures.ps1 -OverwriteExisting`. |
| Expected '$schema' in Report.pbip to follow pattern … pbip/pbipProperties/1.[0-9]+.[0-9]+/schema.json (Power BI Desktop) | .pbip used old `fabric/gitIntegration/itemShortcut/1.0.0/schema.json` | Use `fabric/pbip/pbipProperties/1.0.0/schema.json` in all .pbip files. Report: `products/fabric_powerbi/tooling/page_scaffold_generator/pbip_writer.py` (PBIP_SCHEMA). SemanticModel.pbip in orchestrate: add same `$schema` if Desktop validates it. |
| ReportDefinition: Required artifact is missing … definition.pbir (Power BI Desktop Feb 2026+) | Desktop expects `definition.pbir` at report root; we only had `definition/report.json`. | Generator writes `definition.pbir` with **definitionProperties** schema (version + datasetReference), not report definition. `pbip_writer._write_definition_pbir()`. Doc: `PBIP_REPORT_STRUCTURE.md`. |
| Expected '$schema' in definition.pbir to follow definitionProperties/1.x or 2.x (UnrecognizedSchemaVersion) | We wrote definition.pbir with definition/report/3.0.0 schema; Desktop expects definitionProperties. | Use `definitionProperties/2.0.0/schema.json` and payload: version "4.0", datasetReference.byPath. See samples in `showcases/sample_pbip_report/` and `pbip_writer._write_definition_pbir()`. |
| DatasetDefinition: Required artifact is missing … definition.pbism (Power BI Desktop Feb 2026+) | Desktop expects `definition.pbism` at semantic model root; we only had SemanticModel.pbip and definition/ (TMDL). | Write `definition.pbism` with schema `semanticModel/definitionProperties/1.0.0`, version "4.2", settings {}. Orchestrator does this in the same loop as SemanticModel.pbip. Doc: `PBIP_REPORT_STRUCTURE.md`. |
| Can't resolve schema '1.0.0' in version.json (Power BI Desktop Feb 2026+) | Desktop expects version.json to use **versionMetadata** schema, not **version**. Wrong schema or version value. | Use `$schema`: `fabric/item/report/definition/versionMetadata/1.0.0/schema.json` and `"version": "2.0.0"`. Generator: `pbip_writer.write_version_json()`. Sample: `showcases/sample_pbip_report/.../definition/version.json`. |
| Property 'datasetReference' has not been defined … report.json (schema does not allow additional properties) | We put datasetReference in definition/report.json; the report definition schema does not allow it. | Remove datasetReference from report.json. Dataset binding belongs only in **definition.pbir**. Generator: `pbip_writer.write_report_json()` must not add datasetReference to report_data. Doc: `PBIP_REPORT_STRUCTURE.md`. |
|| `.pbi/localSettings.json` committed; `audit_report_versions.py` reports FORBIDDEN file | Desktop writes user-local state into `.pbi/`; machine-specific, must not be committed. | Add `.pbi/` to `.gitignore` at report level. Remove: `git rm -r --cached "<name>.Report/.pbi/"`. Detected automatically by `audit_report_versions.py`. |
|| Schema URL mismatch in generated files; `check_schema_versions.py` fails | Generator or adapter used a hardcoded schema URL instead of importing from `schema_registry.py`, or registry was updated without regenerating reports. | 1. Verify `schema_registry.py` has correct pinned version. 2. Regenerate reports. 3. Re-run `check_schema_versions.py`. Never hardcode `developer.microsoft.com/json-schemas/fabric` URLs in code. |
|| Cached schema `$id` version mismatch; validator silently checks against wrong rules | `tooling/schemas/pbir/*.schema.json` had an old `$id` version while generators emitted a newer version. | Update `$id` in the cached `.schema.json` to match the version constant in `schema_registry.py`, then run `update_schema_manifest.py`. |
| Semantic model / Report „öffnet mit Fehlern“ oder Schema-Fehler beim Öffnen in Desktop | Fehlendes `$schema` in .pbip (z. B. SemanticModel.pbip nur mit version/artifacts), oder fehlende definition.pbism/pbir. | **Sofort:** Von Repo-Root `.\products\fabric_powerbi\tooling\ensure_pbip_desktop_ready.ps1` ausführen – ergänzt fehlende definition.pbism/pbir und `$schema` in allen .pbip. **Dauerhaft:** Orchestrator schreibt SemanticModel.pbip mit `$schema`; Post-Implementation-Validierung (`pbi_validate_after_impl.ps1`) ruft ensure_pbip_desktop_ready vor den Fabric-Checks auf. |
| TMDL-Validierung schlägt fehl (Syntax/Readiness) | Spaces statt Tabs, description:-Property, oder PBIP-Readiness-Regeln. | **TMDL Script Renderer:** `.\products\fabric_powerbi\tooling\tmdl_render_and_fix.ps1` ausführen. Er prüft TMDL, schreibt Fehler nach `.cursor/tmdl_errors.log`, wendet Auto-Fixes an (Spaces→Tabs, description entfernen) und trägt nach erfolgreichem Fix die Lösung in diese Tabelle ein (Learning Loop). Optional in Pipeline/Validierung einbinden. |
| TMDL "ungültiger Einzug" bei formatString/displayFolder (Desktop Feb 2026, Zeile 21 _Measures) | Measure-Properties (formatString, displayFolder) mit nur **einem Tab** (t1) – Desktop erwartet **zwei Tabs** (t2), also eine Ebene tiefer als die measure-Zeile. | **Generator:** In `Build-MeasureBlock` und `Build-ActionTextMeasureBlock` alle Measure-Properties (formatString, displayFolder, isHidden, annotations) mit **t2** ausgeben. Dann `generate_tmdl_measures.ps1 -OverwriteExisting` und **vor Test** `.\products\fabric_powerbi\tooling\run_fabric_checks.ps1` bzw. `tmdl_render_and_fix.ps1` ausführen. |
| Mixed Tab/Space Indentation in Tabellen-TMDL (dim_*, fact_*); Desktop meldet „ungültiger Einzug" | `table_ops.ps1` oder manuelle Edits fügten Spaces statt Tabs bei Column-Properties ein (z.B. `\t lineageTag:` statt `\t\tlineageTag:`). | **Fix:** Python-Script ersetzt `\t` (Tab+Space) durch korrekte Tab-Indentation in allen 12 Tabellen-TMDL unter `dist/Commercial.SemanticModel/definition/tables/`. **Dauerhaft:** In `table_ops.ps1` nur Tabs verwenden (`$t1 = "\t"`, `$t2 = "\t\t"`). |
| `Gross Margin % vs Plan` DAX-Fehler: Spalte `fact_sales[Plan COGS Amount]` existiert nicht | DAX-Expression referenzierte `fact_sales[Plan COGS Amount]`; diese Spalte existiert nur in `fact_plan_sales` als `Plan Cost of Goods Sold Amount`. | **Fix:** DAX korrigiert: `fact_plan_sales[Plan Cost of Goods Sold Amount]` und `fact_plan_sales[Plan Net Sales Amount]` verwenden. |
| `Promo ROI %` und `Cannibalization %` Fehler: referenzierte Measures fehlen | `Incremental Gross Margin Amount`, `Cannibalized Sales Amount`, `Promo Cost`, `Baseline Sales Amount` waren nie als Measures definiert. | **Fix:** Fehlende Base-Measures in `_Measures.tmdl` ergänzt: `Promo Cost = SUM(fact_promo[Promo Cost])`, `Baseline Sales Amount = SUM(fact_promo[Baseline Sales Amount])`, `Incremental Gross Margin Amount`, `Cannibalized Sales Amount`. |
| Daten-Spalten (integer, decimal etc.) sollen nicht automatisch zusammengefasst werden; Spalten zeigen Summenzeichen / implizite Aufsummierung | Power BI zeigt das Summenzeichen und erlaubt Summe, wenn (1) `summarizeBy: sum` gesetzt ist oder (2) `SummarizationSetBy = Automatic` bei numerischen/aggregierbaren Spalten. Einzelne Dimensionen (z. B. **dim_date.Month**) hatten noch `summarizeBy: sum`; viele Spalten hatten `SummarizationSetBy = Automatic`. **Fact-Tabellen** (z. B. fact_sales): Amount-/Quantity-Spalten hatten ebenfalls `summarizeBy: sum` und Automatic → Summenzeichen. | **Dimensionstabellen:** Jede Spalte `summarizeBy: none` **und** `annotation SummarizationSetBy = User`. **Fact-Tabellen:** Alle Spalten (Keys, Attribute, Amounts, Quantities) auf `summarizeBy: none` und `SummarizationSetBy = User` setzen; Aggregation ausschließlich über Measures in _Measures.tmdl (z. B. [Net Sales Amount] = SUM(fact_sales[Net Sales Amount])). So verschwindet das Summenzeichen auch bei fact_sales (Net Sales Amount, Quantity, Plan Quantity, List Price Amount, Net Price Amount, Discount Amount, Plan Sales Amount, Last Year Sales Amount, Cost of Goods Sold Amount, Plan COGS Amount, Promo Flag, InvoiceLineID). **Generator/Orchestrator:** CreateFromContract und PatchAddSummarizeByNone (table_ops.ps1); bei neuer Fact-Tabelle alle Spalten none + User. |

---

## Report visuals (PBIP / page_scaffold_generator)

| Symptom / message | Cause | Fix |
|------------------|--------|-----|
| Charts (Line/Bar/Waterfall) leer; Felder landen in „Filter für dieses Visual“ statt auf Achse/Werten | queryState nutzte nur eine Rolle `"Data"`; Power BI interpretiert das als Filter. | **Generator:** In `visual_builder.py` für lineChart, clusteredBarChart, waterfallChart rollenspezifische Keys verwenden: `"Category"` (Achse) und `"Y"` (Werte). Dist-Visuals „Net Sales Amount“ und „Variance“ entsprechend anpassen. |
| Tabellen (DetailMatrix, Prescriptive) leer; Felder im Filter statt in Spalten | tableEx nutzte Rolle `"Data"`. | **Generator:** In `visual_builder.py` für tableEx die Rolle `"Values"` verwenden; in `build_table` z. B. `queryState = {"Values": {"projections": ...}}`. Dist DetailMatrix und Prescriptive anpassen. |
| Report öffnet auf Detail statt Overview | Beim Anhängen der Detail-Seite setzte `write_pages_json` `activePageName` auf die neue Seite. | **Generator:** In `pbip_writer.py` bei `append=True` den bestehenden `activePageName` aus der aktuellen `pages.json` beibehalten, nicht überschreiben. |
| Visual-Ordner mit Komma im Namen (z. B. „Net Sales % vs Plan, Delta% …“) verursacht Lade- oder Pfadprobleme | page_builder nutzte measure-abgeleiteten Namen mit `", ".join(measures[:3])`. | **Generator:** In `page_builder.py` wenn der measure-abgeleitete Name `,`, `:`, `\` oder `/` enthält, sicheren slot-basierten Namen verwenden (z. B. „Variance“). Dist: neuer Ordner „Variance“, alter Komma-Name entfernen. |
| Action Panel (T4) zeigt nur Platzhalter | Kein Inhalt aus Action Codes; Generator nutzte statischen Platzhalter. | **Generator:** `ConfigLoader.get_action_panel_content(use_case_id)` aus Bracket `action_code_ids` und Action-Code-YAMLs (Name, Owner, Steps) befüllen. Von scaffold_generator an page_builder übergeben; T4-Panel mit diesem Text füllen. Dist Detail ActionPanel visual.json anpassen. |
| Custom Theme wird im Report nicht erkannt | (1) apply_report_theme schlägt still fehl (z. B. Schema-Validierung), dann fehlen themeCollection.customTheme und resourcePackages in definition/report.json. (2) Report-Pfad relativ, Python löst falsch auf. | **Orchestrator:** Beim Aufruf von apply_report_theme.ps1 `-NoValidate` übergeben, damit Theme-Anwendung nicht an Schema-Validierung scheitert. Report-Pfad als absoluten Pfad übergeben (`[System.IO.Path]::GetFullPath`). **Manuell:** Nach Report-Generierung einmal `apply_report_theme.ps1 -Report <Report-Ordner> -ThemeName "<Theme-Name aus theme_config.json>" -NoValidate` ausführen; prüfen, dass definition/report.json danach themeCollection.customTheme und resourcePackages mit RegisteredResources-Eintrag enthält. |
| python.exe: can't open file '…\@-3' (apply_report_theme.ps1) | (1) PowerShell-Variable `$args` wurde für Skript-Argumente überschrieben; Splat/Launcher übergibt dann falsche argv an Python. (2) Aufruf mit `py -3` + Splat: Launcher reicht `-3` so weiter, dass Python den Skriptpfad als „@-3” interpretiert. | **apply_report_theme.ps1:** Argumente für Python in eigener Variable bauen (z. B. `$scriptArgs`), **nicht** `$args` verwenden. Python-Aufruf: nur `& $pyExe $pyScript @scriptArgs` (kein `-3` beim Aufruf); Python 3 über Version-Check (`py --version` / `python3 --version`) wählen. **Phase5:** Bei Theme-Fehler Phase abbrechen (throw), nicht nur WARNING; nach Apply prüfen, ob report.json `themeCollection.customTheme` mit type RegisteredResources hat. |
| Alle Grid-Pfad-Visuals leer (Main_1, Main_2, Main_3, Detail_Matrix); Felder im Filter statt Field Wells | `_build_base_visual()` in `visual_builder.py` setzte Default `”Data”` queryState-Rolle für **alle** Visuals. Bei Grid-Pfad-Placeholdern (leere columns/measures) wurde die Rolle nie überschrieben → Charts/Tables mit falscher Rolle. | **Generator:** `_build_base_visual()` setzt kein Default-queryState mehr. Jede `build_*`-Methode setzt eigene korrekte Rolle: Charts = `Category`+`Y`, Tables = `Values`, Cards = `Data`, Scatter = `X`+`Y`. Neuer `visual_validator.py` prüft Rollen vor dem Schreiben (Self-Validation). Reports neu generiert mit `--force-full`. |

---

## Semantic model (relationships, layout)

| Symptom / message | Cause | Fix |
|------------------|--------|-----|
| fact_sales nicht mit Dimensionen verknüpft; Modell unvollständig | In relationships.tmdl nur dim_date→LocalDateTable; keine Beziehungen Fact→Dim. | In `definition/relationships.tmdl` eintragen: fact_sales.DateKey→dim_date.DateKey, OrgKey→dim_org.OrgKey, ProductKey→dim_product.ProductKey, CustomerKey→dim_customer.CustomerKey. Bestehende dim_date→LocalDateTable beibehalten. Bei Regeneration: Generator oder Post-Step muss diese Beziehungen ausgeben. |
| Modell-Ansicht (Diagramm) unstrukturiert / Spaghetti | Kein diagramLayout.json oder falsche Positionen. | `diagramLayout.json` im Semantic-Model-Root anlegen: _Measures (0,0), Facts horizontal y=0 (z. B. fact_sales x=280), Dimensionen vertikal x=0 mit 120px Abstand (dim_date, dim_org, dim_product, dim_customer, _ActionReady_Logic, Datumstabellen). Reihenfolge nach Verbindungsanzahl. Validierung: `check_diagram_layout.ps1`. |

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
| pbi-tools compile runs "successful", but generated PBIX contains no `Report/Layout` | The report had only partial PbixProj compatibility (`Version.txt` and placeholder metadata), but no mirrored legacy `Report/report.json` plus `Report/sections/.../visualContainers/...` tree. pbi-tools can emit a shell PBIX without real layout in that case. | Treat compile compatibility as requiring **all** of `Version.txt`, `ReportMetadata.json`, `ReportSettings.json`, and `Report/report.json`. Generator: mirror the legacy `Report` tree from `definition/report.json` and `definition/pages/*/visuals/*` via `pbip_writer.sync_legacy_report_folder()`. Existing dist artifacts: repair with `ensure_pbip_desktop_ready.ps1` (`Sync-LegacyPbixProjReport`). |

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

## Measures (shared domain model, multi–use case)

| Symptom / message | Cause | Fix |
|------------------|--------|-----|
| Measures für COM-001 verschwinden, wenn Orchestrator nur für COM-002 läuft | Phase 2 übergab nur die **ausgewählten** Use-Case-IDs (z. B. COM-002) an generate_tmdl_measures.ps1; _Measures.tmdl wurde mit nur diesem UC überschrieben. | **Orchestrator:** Pro Domain **alle** Use-Case-IDs dieser Domain aus dem Repo übergeben (`$byDomainAll = Get-UseCaseIdsGroupedByDomain -UseCaseIds $allIdsFromRoot`), nicht nur `$byDomain[$domainName]`. So enthält _Measures.tmdl kumulativ alle Measures (COM-001, COM-002, …). **Measure-Skript:** Im konsolidierten Modus nach KPI-ID deduplizieren (`$seenKpiIds`); gleicher KPI in mehreren UCs → nur ein Measure. |

---

## Scripts / Generator (PowerShell, Python)

| Symptom / message | Cause | Fix |
|------------------|--------|-----|
| Stage 1 fails in `check_validate_data_contracts.ps1` with `Python wurde nicht gefunden; ... Microsoft Store ... App-Ausführungsaliase` although `py -3` works | Script only checked command availability / exit code loosely and could still fall through to the broken Windows Store `python` alias. | In `tooling/validation/check_validate_data_contracts.ps1` validate the launcher by reading `--version` output and accepting only interpreters whose output matches `Python 3`. Prefer `py -3`; do not trust the Store alias `python`. |
| Stage 1 fails in `check_data_contract_kpi_coverage.ps1` with `Ungültiger Variablenverweis` at a string like `$ucId:` | In PowerShell double-quoted strings, a variable directly followed by `:` can be parsed as an invalid variable reference. | Delimit the variable explicitly, e.g. use `${ucId}: ...` or `$($ucId): ...` in interpolated strings. |
| Stage 1 fails in `check_usecase_page_types.ps1` with `UnexpectedToken`, missing quotes, or parser errors around `page_type` messages | The script used non-ASCII punctuation in a double-quoted string and also interpolated `$ucId:` without delimiting the variable name. | Keep these validation scripts ASCII-only and delimit the variable explicitly, e.g. `${ucId}: ...`; replace typographic dashes with `-`. |
| Stage 1 fails in `check_extended_usecase_readmes.ps1` with parser errors around README/Directory messages containing `â€”` | The script used typographic dash characters inside interpolated PowerShell strings; in this environment they were decoded incorrectly and broke parsing. | Keep Stage-1 PowerShell validators ASCII-only; replace typographic dashes with `-` in emitted messages. |
| VS Code workspace tasks fail immediately with `pwsh` not found on Windows | `.vscode/tasks.json` assumed PowerShell 7 (`pwsh`) is installed, but some Windows environments only have Windows PowerShell (`powershell`). | Use `powershell` in workspace tasks unless PowerShell 7 is a hard requirement, or document/install `pwsh` explicitly before relying on those tasks. |
| Unerwartetes Token "```" in Ausdruck (generate_tmdl_measures.ps1, Zeile ~814) | In PowerShell inside **double** quotes, backtick (`` ` ``) escapes the next character; `` "```" `` is parsed incorrectly. | Use **single** quotes for literal backticks: `` $lines += ($t2 + '```') ``. No other change; the script was later updated to not output ``` at all (see TMDL measure row above). |

---

## Studio (Next.js / TypeScript) — ActionReady Studio

| Symptom / message | Cause | Fix |
|------------------|--------|-----|
| `next build` exits with "Another next build process is already running" | Stale `.next` build lock from killed process | `pkill -9 -f "next build"` then retry. If lock file persists, `rm -rf studio/.next` and rebuild. |
| `npm run build` is killed (OOM / exit 137) in CI or low-RAM environment | Turbopack full build requires >2 GB RAM | Use `node_modules/.bin/tsc --noEmit -p tsconfig.json` for fast type-only validation. Full build works but may need 4 GB+ RAM. |
| `TS2741: Property 'spines' is missing in type '...' but required in type 'Props'` | Client component Props updated (e.g. `spines: DecisionSpine[]`) before server page updated its JSX render call | Update the server `page.tsx` to load the new data in `Promise.all` and pass it as a prop. Pattern: load → destructure → pass. |
| `TS2322: Property 'X' does not exist on type 'IntrinsicAttributes & Props'` after adding a prop to a client component | The `Props` interface was updated but a parent page still passes the old prop set | Find all callers of the component with `grep -r "ComponentName" src/` and add the missing prop or mark it optional with `?`. |
| `client-only` import error: `node:fs` imported in a Client Component | Server loader (uses `readFile` etc.) was imported directly into a `'use client'` file | Move data loading to a Server Component or Route Handler; pass serialized data as props to the client component. |
| `requireAuth` returns `[session, null]` but `session` is `null` in dev | Auth middleware not running in dev when `AUTH_SECRET` is unset | Set `AUTH_SECRET=dev-secret` in `studio/.env.local`. |
| SSE stream from `/api/ai/chat` returns chunks with `0:` prefix | Vercel AI SDK `toTextStreamResponse()` uses data-stream protocol not raw text | Consumer must strip the `0:"..."` envelope: split on `\n`, filter lines starting with `0:`, parse inner JSON string. Or use `toTextStreamResponse()` directly and read plain text chunks. |
| `AiAssistDrawer` suggestions never parse (stays in loading state) | LLM returned suggestions not starting with `1.` / `2.` / `3.` format | Prompt explicitly instructs numbered list. If model deviates, fall back to splitting on `\n\n` and treating each paragraph as a suggestion. |
| `loadFactsheet()` returns `null` for all brackets | `CORE_USECASES_DIR` resolved incorrectly (CWD mismatch) | In Route Handlers, `process.cwd()` is the project root. Path must be `join(process.cwd(), '..', 'core', 'usecases', 'core')` when Next.js app is in `studio/` subdirectory. Verify with `console.log(process.cwd())` in a GET handler. |
| `color-mix(in srgb, #hex ...)` doesn't respond to dark-mode toggle | Hardcoded hex inside `color-mix()` bypasses the CSS token system | Replace hex argument with `var(--bg)` or equivalent token: `color-mix(in srgb, var(--bg) 92%, var(--accent) 8%)`. |

| `generate_missing_facts.py` or `fix_bracket_component30s.py` not found | Scripts archived to `internal/archive/` after their one-time purpose was complete | Check `internal/archive/tooling/maintenance/` or `internal/archive/showcases/gold_maintenance/` for historical reference. Gold fact Parquet is committed; brackets are clean. |
| Stage 1 exits with code 0 even when a Python check fails | `exit 0` was hardcoded at the end of `run_stage1_checks.ps1` instead of checking `$overallStatus` | Changed final `exit 0` to `if ($overallStatus -eq "fail") { exit 1 }` + message. Also fixed Python launcher to prefer `py -3` over bare `python` (avoids Windows Store alias). |
| GitHub CI `catalog-tmdl-drift` job duplicates what Stage 1 already checks | Stage 1 PS1 runs `check_catalog_tmdl_drift.py`; a separate standalone job ran the same script on ubuntu-latest | Removed standalone `catalog-tmdl-drift` job from `stage1.yml`; kept as sole gate inside Stage 1 PS1. |
| `drift_report.json` artifact uploaded from wrong job | Artifact was uploaded in `catalog-tmdl-drift` job which ran on ubuntu-latest; the file is generated by Stage 1 on windows-latest | Moved artifact upload into the `stage1` job (`if: always()`) in `stage1.yml`. |
| `registry_builder --strict` ran twice per CI run | `python-checks` job called `registry_builder.py --strict` AND Stage 1 runs `check_registry_builder.ps1` | Removed duplicate from `python-checks` job; canonical execution is inside Stage 1 PS1. |

---

| `dim_org` table empty / all columns blank when opening PBIP in Desktop | Gold Layer parquet was regenerated with new schema (`OrgName, OrgLevel, OrgType, Country`) but `dim_org.tmdl` still referenced old columns (`Location, Region, Channel, Customer`) as sourceColumns. M partition picked the newer `.snappy.parquet` (sorts before `part-00000.parquet` alphabetically), which has no matching columns. | Updated `dim_org.tmdl` sourceColumns to match new parquet schema. Added date-sorted file selection (`Table.Sort` by Date modified) and `_delta_log` folder exclusion. Legacy alias columns kept with hidden flag. |
| `DataViewMappingError_ConditionRangeTooLarge` in reports using `dim_org` | `dim_org` had 0 rows (empty due to schema mismatch); Power BI creates invalid condition-range mappings for visuals bound to empty dimension tables, triggering this error. | Fix root cause: align `dim_org.tmdl` sourceColumns with actual parquet schema so dim_org loads correctly (534 rows). Error disappears once the dimension table has data. |
| `check_tmdl_vs_measure_dictionary.ps1` reports `Active Actions Text (DOM)`, `Last Refresh (DOM)`, `Narrative Text (DOM)` as "missing in Measure Dictionary" | These utility measures are framework-generated, not from the KPI catalog, so they're absent from Measure Dictionaries by design. | Extended the exclusion regex in `check_tmdl_vs_measure_dictionary.ps1` to skip measures matching `^(Active Actions Text|Last Refresh|Narrative Text)\b`. |
| `dax.format.forbidden` BPA rule fires on Action_*_Text, Narrative Text, Last Refresh measures that use `FORMAT()` | These text-returning measures legitimately use `FORMAT()` in string concatenation (e.g. `"DIO: " & FORMAT(_val, "0.0")`). The BPA rule was too broad. | Added `allowWhenContains: ["& FORMAT(", "& FORMAT ("]` to the `dax.format.forbidden` rule in `bpa-rules-dax.json`. FORMAT() in string concatenation is allowed. |
| `check_page_template_compliance.py` warns for bracket visual_type `line_chart` and `bar_chart_horizontal` not matching any visual | VISUAL_TYPE_MAP only had `trend_line` and `bar_chart` as map keys; `line_chart` and `bar_chart_horizontal` are valid bracket terms but not aliased. | Added `line_chart` and `bar_chart_horizontal` as aliases in VISUAL_TYPE_MAP. Both map to the same PBIP visual types as `trend_line` / `bar_chart`. |

## Updating this list (Pflicht in jeder Erstellungs-/Fix-Schleife)

**In jeder Erstellungs- oder Fix-Schleife:** Sobald ein Fehler behoben wurde (egal ob aus Pipeline, Desktop, Nutzerbericht oder eigener Analyse), **muss** geprüft werden, ob diese Fehlerklasse bereits in einer Tabelle oben steht. Wenn **nicht**: sofort eine neue Zeile (Symptom | Cause | Fix) in die passende Sektion eintragen. So werden dieselben Fehler nicht wiederholt.

Konkret:

1. Nach jedem Fix: Eintrag in die passende Tabelle (oder neue Sektion) mit **Symptom / Meldung | Ursache | Fix**.
2. Fehler aus `last_run_state.json`, `build_errors.json`, `.cursor/pbi_errors.log` oder Nutzerfeedback: gleiche Regel.
3. Wenn der Fehler durch eine Regel/Check abfangbar ist: Check in `run_fabric_checks.ps1` oder Validierungs-Skripten ergänzen/aktualisieren, damit der nächste Lauf früh mit klarer Meldung abbricht.
