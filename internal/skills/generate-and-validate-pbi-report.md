# Generate and Validate Power BI Report

Iterativer, lernender Workflow für die fehlerfreie Erstellung von Power BI Reports und Semantic Models. Jeder generierte Report wird vor dem Schreiben automatisch validiert. Neue Fehlerklassen werden persistent dokumentiert, damit sie sich nicht wiederholen.

Dieses Dokument ist **tool-agnostisch** -- es kann von jedem AI-Tool (Claude Code, Cursor, Copilot, etc.) und von Menschen gleichermaßen verwendet werden.

## Wann verwenden

- Power BI Report erstellen oder neu generieren
- Semantic Model mit Measures aufbauen oder aktualisieren
- Nach Änderungen an UseCase_Bracket.yaml die Reports aktualisieren
- Report-Fehler systematisch beheben und den Generator verbessern

## Workflow

### 1. Vorbereitung

1. **KNOWN_ERRORS_AND_FIXES.md lesen** (`internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`)
   - Bekannte Fehler und Lösungen durchsehen
   - Insbesondere die Sektionen "Report visuals" und "TMDL / PBIP" beachten

2. **UseCase_Bracket.yaml prüfen** (`core/usecases/core/<ID>/UseCase_Bracket.yaml`)
   - `orchestration.strategic_kpi_id` gesetzt?
   - `orchestration.influencing_kpi_ids` vollständig?
   - `ux_layout_rules.page_1_summary` und `page_2_execution` definiert?
   - `orchestration.action_code_ids` (für T4-Templates)

3. **KPI-Katalog prüfen** (`core/kpi_catalog/`)
   - Alle in Bracket referenzierten KPIs existieren im Katalog
   - DAX-Expressions gültig (keine `:=`, keine `ISERROR`)
   - Base-Measures vorhanden (z.B. `SUM(fact_sales[Net Sales Amount])`)

### 2. Semantic Model generieren/validieren

```bash
# Vollständiger Orchestrator (empfohlen)
.\products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1 -UseCase <ID> -UseAuroraData

# Oder nur Measures generieren
.\tooling\generation\generate_tmdl_measures.ps1 -UseCase <ID>
```

**Validierung:**
```bash
.\products\fabric\powerbi\tooling\run_fabric_checks.ps1
```

Prüfpunkte:
- TMDL nur mit Tabs (keine Spaces)
- Alle Measures im KPI-Katalog vorhanden
- DAX-Spaltenreferenzen zeigen auf existierende Spalten/Tabellen
- `summarizeBy: none` für alle Dimensionsspalten

### 3. Report generieren

```bash
python products/fabric/powerbi/tooling/page_scaffold_generator/generate_full_report.py \
  --use-case <ID> --force-full
```

Der Generator führt automatisch **Self-Validation** durch (`visual_validator.py`):
- queryState-Rollen korrekt (Charts: Category+Y, Tables: Values, Cards: Data)
- Alle Pflichtfelder vorhanden ($schema, name, position, visualType)
- Visual-Namen ordner-sicher (kein `,` `:` `\` `/`)
- Positionen innerhalb Canvas-Grenzen
- Sprechende Namen (kein hex-ID-Fallback)

Bei Fehlern: Generator wirft `ValueError` mit klarer Fehlermeldung → **Schritt 5**.

### 4. Post-Generation Validierung

```bash
.\tooling\pbi_validate_after_impl.ps1 -IncludeDesktopLogMinutes 10 \
  -ResultFile .cursor/pbi_validate_result.json
```

Ergebnis auswerten:
- `success === true` → Weiter zu **Schritt 7**
- `success === false` → **Schritt 5**

### 5. Lernschleife (Fehler beheben)

1. **Fehler analysieren**: Fehlermeldung aus Generator, Validierung oder Power BI Desktop
2. **KNOWN_ERRORS_AND_FIXES.md prüfen**: Ist dieses Muster bereits dokumentiert?
   - **Ja**: Dokumentierte Lösung anwenden
   - **Nein**: Ursache analysieren (Generator-Code, Bracket, KPI-Katalog, TMDL)
3. **Fix anwenden**:
   - Wenn Fehler in generierten Dateien: Dateien korrigieren
   - Wenn Fehler im Generator: → **Schritt 6**
4. **PFLICHT: Neue Fehlerklasse dokumentieren**
   - In `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` neue Zeile eintragen:
   - `| Symptom/Meldung | Ursache | Fix |`
5. **Re-validieren**: Zurück zu Schritt 3 oder 4 (max 5 Iterationen)

### 6. Generator-Fix (bei Bug im Generator)

1. Bug im Generator-Code lokalisieren (meistens in `visual_builder.py`, `page_builder.py`, `pbip_writer.py`)
2. Fix implementieren
3. **Test hinzufügen** in `tests/test_visual_validator.py` oder `tests/test_scaffold_generator.py`
4. Tests ausführen:
   ```bash
   python -m pytest products/fabric/powerbi/tooling/page_scaffold_generator/tests/ -v
   ```
5. **Alle Reports neu generieren** (Schritt 3 für jeden Use Case)
6. KNOWN_ERRORS_AND_FIXES.md aktualisieren

### 7. Abschluss

- [ ] Alle Tests grün
- [ ] `run_fabric_checks.ps1` bestanden (wenn Semantic Model geändert)
- [ ] Kein Visual mit falscher queryState-Rolle
- [ ] TMDL: nur Tabs, kein Mixed Indentation
- [ ] KNOWN_ERRORS_AND_FIXES.md aktuell
- [ ] Commit mit klarer Beschreibung

## Validierungscheckliste

### Report Visuals
- [ ] Charts (lineChart, waterfallChart, clusteredBarChart, etc.): queryState hat `Category` + `Y`
- [ ] Tables (tableEx): queryState hat `Values`
- [ ] Cards (cardVisual): queryState hat `Data`
- [ ] Matrix (pivotTable): queryState hat `Rows` + `Values`
- [ ] Scatter (scatterChart): queryState hat `X` + `Y`
- [ ] Kein Visual verwendet `"Data"` Rolle außer cardVisual und textbox

### PBIP-Struktur
- [ ] `definition.pbir` vorhanden mit `definitionProperties/2.0.0` Schema
- [ ] `report.json` ohne `datasetReference` (gehört nur in definition.pbir)
- [ ] `version.json` mit `versionMetadata/1.0.0` Schema und version `2.0.0`
- [ ] `.pbip` mit `pbipProperties/1.0.0` Schema
- [ ] Visual-Ordner ohne Sonderzeichen (`,` `:` `\` `/`)
- [ ] Sprechende Seitennamen (z.B. `Page_COM001_Overview`)

### Semantic Model
- [ ] Alle TMDL-Dateien: nur Tabs, kein Mixed Indentation
- [ ] `formatString`/`displayFolder` mit 2 Tabs (Measure-Ebene)
- [ ] Alle referenzierten Measures existieren in `_Measures.tmdl`
- [ ] Alle DAX-Spaltenreferenzen zeigen auf existierende Spalten
- [ ] `summarizeBy: none` + `SummarizationSetBy = User` für alle Spalten
- [ ] `model.tmdl` hat `ref table` für jede Tabelle in `definition/tables/`

## Fehlerbehandlung (Quick Reference)

| Fehlertyp | Erste Aktion |
|-----------|-------------|
| queryState falsch | `visual_builder.py` prüfen -- welche Rolle setzt `build_*`? |
| TMDL Indentation | `tmdl_render_and_fix.ps1` ausführen |
| Fehlende Measure | KPI-Katalog prüfen, ggf. Base-Measure anlegen |
| DAX-Spalte nicht gefunden | Spaltenname in Tabellen-TMDL prüfen |
| Theme nicht erkannt | `apply_report_theme.ps1` manuell mit `-NoValidate` |
| definition.pbir fehlt | `ensure_pbip_desktop_ready.ps1` ausführen |
| Report öffnet auf Detail | `pages.json` prüfen: `activePageName` muss Overview sein |

## Key Paths

| Artefakt | Pfad |
|----------|------|
| Generator | `products/fabric/powerbi/tooling/page_scaffold_generator/` |
| Self-Validation | `products/fabric/powerbi/tooling/page_scaffold_generator/visual_validator.py` |
| Tests | `products/fabric/powerbi/tooling/page_scaffold_generator/tests/` |
| Generated Reports | `products/fabric/powerbi/dist/` |
| Orchestrator | `products/fabric/powerbi/orchestrator/orchestrate_full_model.ps1` |
| Knowledge Base | `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` |
| Fabric Checks | `products/fabric/powerbi/tooling/run_fabric_checks.ps1` |
| Post-Impl Validation | `tooling/pbi_validate_after_impl.ps1` |
| KPI Catalog | `core/kpi_catalog/` |
| Use Case Brackets | `core/usecases/core/<ID>/UseCase_Bracket.yaml` |
| BPA Rules | `tooling/linters/powerbi/bpa-rules-*.json` |
