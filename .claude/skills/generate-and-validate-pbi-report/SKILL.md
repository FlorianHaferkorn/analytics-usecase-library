---
name: generate-and-validate-pbi-report
description: "Generate and validate a Power BI report and semantic model (PBIP/TMDL/PBIR) for a use case in an iterative loop until all checks pass. Use when generating or regenerating a Power BI report from a UseCase_Bracket, building or updating a semantic model with measures, or refreshing reports after UseCase_Bracket.yaml changes."
version: "1.2.0"
license: MIT
source: ALUCA (Analytics Library of Use Cases) — governance overlay
---

<!-- AUTO-GENERATED from docs/agent/skills/ — do not edit; run tooling/generator/generate_tool_configs.py -->

# Generate and Validate Power BI Report

Iterativer, lernender Workflow für die fehlerfreie Erstellung von Power BI Reports und Semantic Models. Jeder generierte Report wird vor dem Schreiben automatisch validiert. Neue Fehlerklassen werden persistent dokumentiert, damit sie sich nicht wiederholen.

Dieses Dokument ist **tool-agnostisch** -- es kann von jedem AI-Tool (Claude Code, Codex, Copilot, etc.) und von Menschen gleichermaßen verwendet werden.

## Wann verwenden

- Power BI Report erstellen oder neu generieren
- Semantic Model mit Measures aufbauen oder aktualisieren
- Nach Änderungen an UseCase_Bracket.yaml die Reports aktualisieren
- Report-Fehler systematisch beheben und den Generator verbessern

## Format

PBIR ist allgemein verfügbar (GA) und das Standardformat für Power-BI-Berichte. Power BI Desktop
konvertiert Berichte im PBIR-Legacy-Format (ein `report.json` mit `sections`/`visualContainers`)
beim Speichern ohne Rückfrage nach PBIR; die Sicherung bleibt 30 Tage (Desktop) bzw. 28 Tage
(Dienst). ALUCA erzeugt nur PBIR: `definition/report.json` (Berichtsmetadaten),
`definition/pages/<Seite>/page.json`, `.../visuals/<Visual>/visual.json`, `definition.pbir`
(D-686, SIG-2609-008).

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
.\tooling\generator\generate_tmdl_measures.ps1 -UseCase <ID>
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

**Pflicht: offizieller PBIR-Validator** (Skills-Abgleich R2, D-687). Microsofts Report-Skill
verlangt `powerbi-report-author validate`; gepinnt ist 0.5.0 wie in
`.github/workflows/superversion.yml` und in Meridian. Ein Report gilt erst als fertig, wenn der
Validator ohne `error` durchläuft.

```bash
npm install -g @microsoft/powerbi-report-authoring-cli@0.5.0   # einmalig; --version muss 0.5.0 sein
powerbi-report-author validate products/fabric/powerbi/dist/<UC>_<Title>.Report --no-schema

# Gleicher Lauf über alle Reports im ALUCA-Gate (Tier 1 nur mit Opt-in):
PBI_QUALITY_ALLOW_EXTERNAL=1 python -m tooling.report_quality.cli --summary
```

**Bewusst offen: Host-Preview mit Screenshot.** Die offizielle Skill schließt erst nach einer
Vorschau im Host mit Screenshot ab. Das braucht Power BI Desktop unter Windows; solange es keinen
Windows-Runner gibt, bleibt dieser Schritt offen und ist kein Abschlusskriterium. Lokal unter
Windows: `tooling/pbi_validate_after_impl.ps1` (unten, optional).

**Desktop-Guard vor dem Schreiben** (R3/R4, D-687): `generate_full_report.py` bricht ab, wenn der
Ziel-Report in Power BI Desktop offen ist (`--allow-desktop-open` übergeht das bewusst), und warnt
bei uncommitteten Änderungen im Ziel. Guard: `products/fabric/powerbi/tooling/desktop_guard.py`
(Peer von Meridian `core/pbi_engine/desktop_guard.py`).

```bash
# Schema drift gate (immer ausführen — prüft alle $schema URLs)
py -3 products/fabric/powerbi/tooling/validation/check_schema_versions.py --explain-known-fix

# Vollständige Fabric-Prüfung (inkl. neuer Schema-Version-Check)
.\products\fabric\powerbi\tooling\run_fabric_checks.ps1

# fab-inspector BPA-Regeln (max Visuals/Seite, kein vertikales Scrollen, Theme-Farben)
# laufen bereits automatisch als Teil von run_fabric_checks.ps1 oben -- kein separater
# Aufruf nötig. check_with_pbi_cli.ps1 ist seit R3.4 deprecated (s. KNOWN_ERRORS_AND_FIXES.md).

# Optional: Desktop-Validierung
.\tooling\pbi_validate_after_impl.ps1 -IncludeDesktopLogMinutes 10 \
  -ResultFile .local/pbi_validate_result.json
```

Ergebnis auswerten:
- Alle Checks grün → Weiter zu **Schritt 7**
- Fehler → **Schritt 5**

### 5. Lernschleife (Fehler beheben) — PFLICHT

Dies ist die wichtigste Phase. Jeder neue Fehler **muss** in eine dauerhafte Prävention umgewandelt werden.

1. **Vor dem Fix**: `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` lesen — ist das Muster bereits dokumentiert?
   - **Ja**: Dokumentierte Lösung direkt anwenden
   - **Nein**: Ursache analysieren (Generator, Bracket, KPI-Katalog, TMDL, Schema-Version)

2. **Fix anwenden**:
   - Fehler in generierten Dateien → Dateien korrigieren
   - Fehler in Generator/Adapter → **Schritt 6**
   - Schema-Drift → `schema_registry.py` prüfen, ggf. `update_schema_manifest.py` ausführen

3. **PFLICHT: Neue Fehlerklasse dauerhaft verhindern** (eines davon):
   - Unit-Test in `tests/` anlegen der den Fehler reproduziert → Fix → Test grün
   - Validator-Regel in `check_schema_versions.py` oder `check_pbir_schema.ps1` ergänzen
   - Generator-Invariante in `visual_validator.py` oder `pbip_writer.py` hinzufügen
   - Schema-Manifest-Update via `update_schema_manifest.py`

4. **PFLICHT: KNOWN_ERRORS_AND_FIXES.md aktualisieren**
   - `| Symptom/Meldung | Ursache | Fix |` in passende Sektion eintragen
   - Befehl der den Fehler zukünftig fängt angeben

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

Automatisch geprüft, keine Handcheckliste (Skills-Abgleich R5, D-687):

| Prüfung | Gate | Lauf |
|---|---|---|
| Jede Measure- und Spaltenbindung existiert im TMDL des gebundenen Modells (`definition.pbir`) | `tooling/report_quality/dax_reference_validator.py` (`dax-reference:missing-measure`, `dax-reference:missing-column`, critical) | `python -m tooling.report_quality.cli --summary`; in `run_fabric_checks.ps1` über `check_report_quality.ps1` |
| Charts und Tabellen haben Projektionen, Pflicht-Slots je Seite | `products/fabric/powerbi/tooling/validate_bindings.py` | CI-Job „Python checks + report bindings“ (`.github/workflows/stage1.yml`) |
| queryState-Rollen je Visual-Typ (Charts `Category`+`Y`, `tableEx` `Values`, `cardVisual` `Data`, `pivotTable` `Rows`+`Values`, `scatterChart` `X`+`Y`) | `page_scaffold_generator/visual_validator.py` | beim Generieren (Self-Validation) |

### PBIP-Struktur
- [ ] `definition.pbir` vorhanden mit `definitionProperties/2.0.0` Schema
- [ ] `report.json` ohne `datasetReference` (gehört nur in definition.pbir)
- [ ] `version.json` mit `versionMetadata/1.0.0` Schema und version `2.0.0`
- [ ] `.pbip` mit `pbipProperties/1.0.0` Schema
- [ ] Visual-Ordner ohne Sonderzeichen (`,` `:` `\` `/`)
- [ ] Sprechende Seitennamen (z.B. `Page_COM001_Overview`)
- [ ] Kein `.pbi/localSettings.json` oder `.pbi/cache.abf` committed
- [ ] `check_schema_versions.py` läuft ohne Fehler (alle `$schema` URLs stimmen mit Registry überein)
- [ ] `schema_manifest.json` ist aktuell (`update_schema_manifest.py --check-only` grün)

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
| **Schema Registry** | `products/fabric/powerbi/tooling/schema_registry.py` |
| **Schema Manifest** | `tooling/schemas/pbir/schema_manifest.json` |
| **Schema Drift Check** | `products/fabric/powerbi/tooling/validation/check_schema_versions.py` |
| **Manifest Updater** | `products/fabric/powerbi/tooling/update_schema_manifest.py` |
| **Migration Audit** | `products/fabric/powerbi/tooling/migration/audit_report_versions.py` |
| **Rename Cascade Audit** | `products/fabric/powerbi/tooling/migration/audit_rename_cascade.py` |
| **fab-inspector BPA Rules** (R3.2, ersetzt pbi-cli Wrapper) | `products/fabric/powerbi/tooling/validation/check_fab_inspector.ps1` |
| **Report Scorecard** (R3.3) | `products/fabric/powerbi/tooling/validation/check_report_scorecard.ps1` |
