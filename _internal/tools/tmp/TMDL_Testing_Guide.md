# TMDL Testing Guide

## 4 Validation-Ebenen für TMDL-Qualitätssicherung

---

## ✅ Ebene 1: Syntaktische Validierung (Automatisiert)

**Tool:** `_internal/tools/tmp/test_tmdl.ps1`

**Was wird geprüft:**
- ✓ Datei existiert
- ✓ UTF-8 ohne BOM (Required für TMDL!)
- ✓ Valide TMDL-Struktur (`table` Keyword)
- ✓ Measures vorhanden
- ✓ Jedes Measure hat `formatString`
- ✓ Jedes Measure hat `displayFolder`
- ✓ Jedes Measure hat `///` Description-Comment
- ✓ Kein `:=` Operator (DAX nutzt `=`)
- ✓ Konsistente Indentation

**Ausführung:**
```powershell
./_internal/tools/tmp/test_tmdl.ps1 -TmdlFile "dist\USE-CASE-ID\*.SemanticModel\definition\tables\_Measures.tmdl"
```

**Beispiel-Output:**
```
=== TMDL Validation Test ===
[PASS] File exists
[PASS] UTF-8 without BOM
[PASS] Valid TMDL structure (table keyword found)
[PASS] Measures found (2)
[WARN] 2 measures missing formatString
[WARN] 2 measures missing displayFolder
[PASS] All measures have /// description
[PASS] No := operator usage

✓ TMDL validation passed!
```

---

## ✅ Ebene 2: Best Practice Analyzer (BPA)

**Tool:** `_internal/tools/linters/run_bpa.ps1` + JSON-Regelkataloge

**Was wird geprüft:**
- ✓ Semantic Model Performance Rules (650+ Zeilen, 40+ Regeln)
  - Floating Point Data Types vermeiden
  - IsAvailableInMdx auf false für Hidden Columns
  - Bi-Directional Relationships gegen High-Cardinality prüfen
  - Long-Length Columns mit High Cardinality reduzieren
- ✓ DAX Style Guide Rules (74 Zeilen)
  - VAR/RETURN Pattern für komplexe Measures
  - DIVIDE() statt `/` für Divide-by-Zero Schutz
  - FORMAT() verboten in computational Measures
  - REMOVEFILTERS statt ALL
  - IF-Nesting vermeiden → SWITCH(TRUE())
- ✓ Report Best Practices
  - Naming Conventions
  - Hidden Objects Management
  - Calculation Dependencies

**Ausführung:**
```powershell
# Für spezifisches Use Case
./_internal/tools/linters/run_bpa.ps1 -Root "dist\COM-001\COM-001.SemanticModel"

# Über run_all_checks.ps1 (umfassend)
./_internal/tools/run_all_checks.ps1
```

**Regelkataloge:**
- `_internal/tools/linters/bpa-rules-semanticmodel.json` - Performance & Maintenance
- `_internal/tools/linters/bpa-rules-dax.json` - DAX Style Guide
- `_internal/tools/linters/bpa-rules-report.json` - Report Best Practices

---

## ✅ Ebene 3: VS Code TMDL Extension (Interaktiv)

**Tool:** Official Analysis Services TMDL Language Service

**Installation:**
```powershell
# VS Code Extension installieren
code --install-extension analysis-services.TMDL
```

**Was wird geprüft:**
- ✓ Live TMDL Syntax Highlighting
- ✓ IntelliSense für TMDL Keywords
- ✓ Real-time Error Diagnostics
- ✓ Auto-Completion für Tabellen/Columns/Measures
- ✓ Hover-Tooltips für Dokumentation

**Workflow:**
1. TMDL-Datei in VS Code öffnen
2. Extension erkennt `.tmdl` automatisch
3. Syntax-Fehler werden rot unterstrichen
4. IntelliSense mit `Ctrl+Space`

**Offizielle Doku:**
- Extension: https://marketplace.visualstudio.com/items?itemName=analysis-services.TMDL
- TMDL Spec: https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview

---

## ✅ Ebene 4: Power BI Desktop Integration Test (End-to-End)

**Tool:** Power BI Desktop mit TMDL View (GA seit Nov 2024)

**Was wird geprüft:**
- ✓ TMDL kann in Power BI Desktop geladen werden
- ✓ Measures sind im Model Browser sichtbar
- ✓ DAX-Expressions evaluieren korrekt
- ✓ Relationships funktionieren
- ✓ Visuals können auf Measures zugreifen
- ✓ Format Strings werden korrekt angewendet

**Workflow:**

### A) Neues Projekt erstellen (PBIP Format):
```powershell
# 1. Semantic Model Folder erstellen
mkdir "test_model"
cd test_model

# 2. PBIP-Struktur aufbauen
mkdir "MyModel.SemanticModel\definition\tables"
mkdir "MyModel.Report"

# 3. TMDL-Dateien kopieren
copy "dist\COM-001\COM-001.SemanticModel\definition\tables\*.tmdl" "MyModel.SemanticModel\definition\tables\"

# 4. model.tmdl erstellen
@"
model Model
  culture: de-DE

  ref table _Measures
"@ | Out-File -Encoding UTF8NoBOM "MyModel.SemanticModel\definition\model.tmdl"

# 5. In Power BI Desktop öffnen
explorer .
```

### B) TMDL View in Power BI Desktop:
1. Power BI Desktop öffnen
2. File → Open → Browse
3. `MyModel.SemanticModel` Ordner auswählen
4. View → TMDL View aktivieren
5. Measures in `tables/_Measures.tmdl` editieren
6. Save → TMDL wird zurückgeschrieben

### C) Validierung in Desktop:
1. Model View öffnen
2. _Measures Tabelle prüfen
3. Measures expandieren
4. DAX-Expressions prüfen (Measure auswählen → Formula Bar)
5. Report View → Visual erstellen mit Measure
6. Format String validieren (Währung, Prozent, etc.)

**Troubleshooting:**

| Problem | Lösung |
|---------|--------|
| TMDL View nicht verfügbar | Power BI Desktop auf neueste Version updaten (TMDL GA seit Nov 2024) |
| Syntax Error beim Laden | `test_tmdl.ps1` ausführen für Details |
| Measure nicht sichtbar | Prüfe `ref table _Measures` in model.tmdl |
| Format String ignoriert | Prüfe Syntax: `formatString: "#,0.00"` (Quotes required) |
| Description fehlt | `///` Comment-Zeilen über measure Block hinzufügen |

---

## 🎯 Empfohlener Test-Workflow

### 1. Während der Entwicklung:
```powershell
# Quick Syntax Check
./_internal/tools/tmp/test_tmdl.ps1 -TmdlFile "path\to\_Measures.tmdl"
```

### 2. Vor Commit:
```powershell
# Umfassende Validierung
./_internal/tools/run_all_checks.ps1
```

### 3. Interaktiv (optional):
- TMDL-Datei in VS Code mit Extension öffnen
- Live Feedback während des Editierens

### 4. End-to-End Test (Showcase):
- PBIP-Projekt erstellen
- In Power BI Desktop laden
- Visual erstellen
- Validieren: Measure funktioniert, Format korrekt

---

## 📊 Beispiel: COM-001 (Sales Performance) testen

```powershell
# Schritt 1: Measures generieren
./_internal/tools/generation/generate_tmdl_measures.ps1 -UseCase "COM-001" -OverwriteExisting

# Schritt 2: Syntax validieren
./_internal/tools/tmp/test_tmdl.ps1 -TmdlFile "dist\COM-001\COM-001.SemanticModel\definition\tables\_Measures.tmdl"

# Schritt 3: BPA ausführen
./_internal/tools/run_all_checks.ps1

# Schritt 4: In Power BI Desktop öffnen
explorer "dist\COM-001"
# Dann: File → Open → COM-001.SemanticModel in Power BI Desktop
```

---

## 🔍 Qualitätsmetriken

| Ebene | Check-Typ | Geschwindigkeit | Abdeckung | Automatisierbar |
|-------|-----------|-----------------|-----------|-----------------|
| 1. Syntaktisch | Struktur, Encoding | < 1s | Basis | ✅ Ja |
| 2. BPA | Style, Performance | < 5s | Umfassend | ✅ Ja |
| 3. VS Code | Live Feedback | Real-time | Syntax + IntelliSense | ⚠️ Interaktiv |
| 4. Power BI | End-to-End | Manual | Vollständig | ❌ Nein |

**Empfehlung:** 
- **CI/CD**: Ebene 1 + 2 (automatisiert)
- **Dev Workflow**: Ebene 3 (VS Code Extension)
- **Showcase Validation**: Ebene 4 (Power BI Desktop)

---

## 📚 Referenzen

### Microsoft Official:
- TMDL Overview: https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview
- TMDL How-To: https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-how-to
- Power BI TMDL View: https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-tmdl-view
- PBIP Semantic Model: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset
- VS Code Extension: https://marketplace.visualstudio.com/items?itemName=analysis-services.TMDL

### Internal:
- [TMDL Official Refs](../docs/operating_model/reference/TMDL_Official_Refs.md)
- [TMDL Allowed Subset](../docs/operating_model/reference/TMDL_Allowed_Subset.md)
- [KPI Catalog](../framework/kpi_catalog/KPI_Catalog.md)
- [Measure System](../docs/operating_model/measure_system.md)

---

**Last Updated:** 02.02.2026
