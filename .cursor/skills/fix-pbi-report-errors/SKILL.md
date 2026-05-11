<!-- AUTO-GENERATED from docs/agent/ â€” do not edit directly. Run: python tooling/agent/generate_tool_configs.py -->

---
name: fix-pbi-report-errors
description: Diagnose and fix Power BI report and semantic model errors. Tool-agnostic workflow for any AI tool or human.
version: "1.1.0"
---

# Fix Power BI Report Errors

Diagnose- und Reparatur-Workflow fÃ¼r Fehler in Power BI Reports und Semantic Models. Jeder Fix wird in der Knowledge Base dokumentiert, damit sich Fehler nicht wiederholen.

Dieses Dokument ist **tool-agnostisch** -- es kann von jedem AI-Tool (Claude Code, Cursor, Copilot, etc.) und von Menschen gleichermaÃŸen verwendet werden.

## Wann verwenden

- Power BI Desktop zeigt Fehler beim Ã–ffnen eines Reports
- Visuals sind leer, Felder landen im Filter statt in Field Wells
- TMDL-Validierung schlÃ¤gt fehl
- Measures fehlen oder DAX-Fehler
- Pipeline/Orchestrator meldet Fehler
- `.cursor/pbi_errors.log` enthÃ¤lt neue EintrÃ¤ge

## Workflow

### 1. Fehler erfassen

**Quellen fÃ¼r Fehlermeldungen:**

| Quelle | Pfad |
|--------|------|
| Power BI Desktop (live) | `.cursor/pbi_errors.log` (via `watch_pbi.ps1`) |
| Pipeline | `products/fabric/powerbi/orchestrator/last_run_state.json` |
| Build Errors | `products/fabric/powerbi/orchestrator/out/build_errors.json` |
| Quality Checks | `internal/reviews/run_all_checks_failures.json` |
| Post-Impl Validation | `.cursor/pbi_validate_result.json` |

### 2. Knowledge Base prÃ¼fen

**Vor jeder Analyse:** `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` durchsuchen.

Ist das Fehlermuster bereits dokumentiert?
- **Ja**: Dokumentierte LÃ¶sung anwenden â†’ Schritt 4
- **Nein**: Weiter mit Schritt 3

### 3. Fehler-Triage

#### Report-Fehler (Visuals, Layout, PBIP-Struktur)

| Symptom | Wahrscheinliche Ursache | Wo suchen |
|---------|------------------------|-----------|
| Visuals leer, Felder im Filter | Falsche queryState-Rolle (`Data` statt `Values`/`Category`+`Y`) | `visual_builder.py` / generierte `visual.json` |
| Report Ã¶ffnet auf falscher Seite | `activePageName` in `pages.json` Ã¼berschrieben | `pbip_writer.py` / `pages.json` |
| Schema-Fehler beim Ã–ffnen | Fehlende/falsche `$schema` in `.pbip`, `definition.pbir`, `version.json` | `pbip_writer.py` / generierte JSON-Dateien |
| `datasetReference` Fehler | `datasetReference` in `report.json` statt in `definition.pbir` | `pbip_writer.py` |
| Visual-Ordner nicht ladbar | Sonderzeichen im Ordnernamen (`,` `:` etc.) | `page_builder.py` |
| Theme nicht erkannt | `apply_report_theme.ps1` fehlgeschlagen | `report.json` â†’ `themeCollection.customTheme` |

#### Semantic Model Fehler (TMDL, DAX, Relationships)

| Symptom | Wahrscheinliche Ursache | Wo suchen |
|---------|------------------------|-----------|
| TMDL Indentation Error | Spaces statt Tabs oder Mixed Indentation | `*.tmdl` Dateien in `definition/tables/` |
| `formatString` ungÃ¼ltiger Einzug | Nur 1 Tab statt 2 Tabs bei Measure-Properties | `_Measures.tmdl`, `generate_tmdl_measures.ps1` |
| Measure nicht gefunden | Base-Measure nicht als KPI angelegt | `core/kpi_catalog/`, `_Measures.tmdl` |
| DAX Spalte nicht gefunden | Falsche Tabelle/Spalte in DAX-Expression | `_Measures.tmdl`, Tabellen-TMDL |
| Duplicate Measure | Measure in `_Measures.tmdl` UND `_ActionReady_Logic.tmdl` | `generate_tmdl_measures.ps1` |
| Modell unvollstÃ¤ndig | Fehlende `ref table` in `model.tmdl` | `model.tmdl` |
| Keine Relationships | `relationships.tmdl` fehlt oder unvollstÃ¤ndig | `relationships.tmdl` |

### 4. Fix anwenden

#### Quick-Fixes (hÃ¤ufigste Probleme)

**TMDL Indentation:**
```bash
.\products\fabric\powerbi\tooling\tmdl_render_and_fix.ps1
```

**Fehlende PBIP-Struktur (definition.pbir, definition.pbism, $schema):**
```bash
.\products\fabric\powerbi\tooling\ensure_pbip_desktop_ready.ps1
```

**Report-Visuals mit falscher queryState-Rolle:**
1. PrÃ¼fen ob `visual_builder.py` den Bug enthÃ¤lt (Schritt 5)
2. Oder direkt in der generierten `visual.json` die Rolle Ã¤ndern:
   - Charts: `"Data"` â†’ `"Category"` + `"Y"`
   - Tables: `"Data"` â†’ `"Values"`

**Fehlende Measures:**
1. KPI im Katalog anlegen (`core/kpi_catalog/`)
2. Measures regenerieren: `.\\tooling\\generator\\generate_tmdl_measures.ps1 -UseCase <ID> -OverwriteExisting`

### 5. Generator-Fix (wenn Bug im Generator)

Wenn der Fehler nicht in den generierten Dateien liegt, sondern im Generator-Code:

1. **Ursache im Generator lokalisieren**:
   - `visual_builder.py`: queryState-Rollen, Visual-Struktur
   - `page_builder.py`: Layout, Slot-Zuordnung, Fallback-Visuals
   - `pbip_writer.py`: Dateistruktur, JSON-Schemas
   - `config_loader.py`: Bracket-Parsing, KPI-AuflÃ¶sung
   - `slicer_builder.py`: Slicer-Konfiguration

2. **Fix implementieren**

3. **Test hinzufÃ¼gen** (Pflicht!):
   ```bash
   # In tests/test_visual_validator.py oder tests/test_scaffold_generator.py
   python -m pytest products/fabric/powerbi/tooling/page_scaffold_generator/tests/ -v
   ```

4. **Reports neu generieren**:
   ```bash
   python products/fabric/powerbi/tooling/page_scaffold_generator/generate_full_report.py \
     --use-case COM-001 --force-full
   # FÃ¼r alle Use Cases wiederholen
   ```

### 6. Validierung

```bash
# Report-Validierung
.\tooling\pbi_validate_after_impl.ps1 -ResultFile .cursor/pbi_validate_result.json

# Fabric Checks (TMDL, DAX, Measures)
.\products\fabric\powerbi\tooling\run_fabric_checks.ps1

# Generator-Tests
python -m pytest products/fabric/powerbi/tooling/page_scaffold_generator/tests/ -v
```

### 7. Knowledge Base aktualisieren (PFLICHT)

**Nach jedem Fix einer neuen Fehlerklasse:**

In `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` eine neue Zeile in der passenden Sektion eintragen:

```markdown
| <Symptom / Fehlermeldung> | <Ursache> | <Fix (inkl. Datei/Script)> |
```

**Sektionen:**
- `## TMDL / PBIP` -- Indentation, Schema, Struktur
- `## Report visuals` -- queryState, Layout, Theme
- `## Semantic model` -- Relationships, Diagramm
- `## DAX / measures` -- Syntax, fehlende Measures
- `## datasetReference` -- Datenbindung
- `## Scripts / Generator` -- PowerShell/Python Bugs

Wenn der Fehler durch einen automatischen Check abgefangen werden kann: Check in `run_fabric_checks.ps1` oder `visual_validator.py` ergÃ¤nzen.

## Diagnose-Hilfen

### queryState-Rollen-Referenz

| Visual Type | Korrekte Rollen | Falsch (hÃ¤ufig) |
|-------------|----------------|-----------------|
| lineChart, waterfallChart, clusteredBarChart | Category + Y | Data |
| tableEx | Values | Data |
| pivotTable | Rows + Values | Data |
| cardVisual | Data | -- |
| scatterChart | X + Y | Data |
| slicer | Values | Data |
| textbox | (keine) | -- |

### TMDL Indentation-Referenz

```
table 'fact_sales'                          â† 0 Tabs
â†’   lineageTag: abc-123                     â† 1 Tab (Tabellen-Property)
â†’   partition 'fact_sales' = m              â† 1 Tab
â†’   â†’   source = ...                        â† 2 Tabs
â†’   column 'Net Sales Amount'               â† 1 Tab
â†’   â†’   dataType: decimal                   â† 2 Tabs (Spalten-Property)
â†’   â†’   summarizeBy: none                   â† 2 Tabs
â†’   â†’   annotation SummarizationSetBy = Userâ† 2 Tabs
â†’   measure 'Net Sales' = SUM(...)          â† 1 Tab
â†’   â†’   formatString: #,##0                 â† 2 Tabs (Measure-Property)
â†’   â†’   displayFolder: 1_Revenue            â† 2 Tabs
```

## Key Paths

| Artefakt | Pfad |
|----------|------|
| Knowledge Base | `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` |
| Generator | `products/fabric/powerbi/tooling/page_scaffold_generator/` |
| Self-Validation | `products/fabric/powerbi/tooling/page_scaffold_generator/visual_validator.py` |
| Generated Reports | `products/fabric/powerbi/dist/` |
| TMDL Fix Script | `products/fabric/powerbi/tooling/tmdl_render_and_fix.ps1` |
| PBIP Fix Script | `products/fabric/powerbi/tooling/ensure_pbip_desktop_ready.ps1` |
| Fabric Checks | `products/fabric/powerbi/tooling/run_fabric_checks.ps1` |
| BPA Rules | `tooling/linters/powerbi/bpa-rules-report.json`, `bpa-rules-tmdl.json`, `bpa-rules-dax.json` |
| Error Log (Desktop) | `.cursor/pbi_errors.log` |
| Error Watcher | `watch_pbi.ps1` |

