# TMDL Testing Guide

## 4 Validation-Ebenen für TMDL-Qualitätssicherung

---

## Ebene 1: Syntaktische Validierung (Automatisiert)

**Tool:** `products/fabric/powerbi/tooling/test_tmdl.ps1`

**Was wird geprüft:**
- Datei existiert
- UTF-8 ohne BOM (Required für TMDL!)
- Valide TMDL-Struktur (`table` Keyword)
- Measures vorhanden
- Jedes Measure hat `formatString`
- Jedes Measure hat `displayFolder`
- Jedes Measure hat `///` Description-Comment
- Kein `:=` Operator (DAX nutzt `=`)
- Konsistente Indentation

**Ausführung (von Repo-Root):**
```powershell
./products/fabric/powerbi/tooling/test_tmdl.ps1 -TmdlFile "products\fabric/powerbi\dist\USE-CASE-ID\USE-CASE-ID.SemanticModel\definition\tables\_Measures.tmdl"
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

TMDL validation passed!
```

---

## Ebene 2: Best Practice Analyzer (BPA)

**Tool:** `tooling/linters/run_bpa.ps1` + JSON-Regelkataloge

**Was wird geprüft:**
- Semantic Model Performance Rules (650+ Zeilen, 40+ Regeln)
- DAX Style Guide Rules (74 Zeilen)
- Report Best Practices

**Ausführung (von Repo-Root):**
```powershell
# Für spezifisches Use Case
./tooling/linters/run_bpa.ps1 -Root "products\fabric/powerbi\dist\COM-001\COM-001.SemanticModel"

# Über run_all_checks.ps1 (umfassend)
./tooling/run_all_checks.ps1
```

**Regelkataloge:**
- `tooling/linters/bpa-rules-semanticmodel.json`
- `tooling/linters/bpa-rules-dax.json`
- `tooling/linters/bpa-rules-report.json`

---

## Ebene 3: VS Code TMDL Extension (Interaktiv)

**Tool:** Official Analysis Services TMDL Language Service

**Installation:**
```powershell
code --install-extension analysis-services.TMDL
```

**Workflow:**
1. TMDL-Datei in VS Code öffnen
2. Extension erkennt `.tmdl` automatisch
3. Syntax-Fehler werden rot unterstrichen
4. IntelliSense mit `Ctrl+Space`

**Offizielle Doku:**
- Extension: <https://marketplace.visualstudio.com/items?itemName=analysis-services.TMDL>
- TMDL Spec: <https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview>

---

## Ebene 4: Power BI Desktop Integration Test (End-to-End)

**Tool:** Power BI Desktop mit TMDL View (GA seit Nov 2024)

**Workflow:**
1. Power BI Desktop öffnen
2. File → Open → Browse
3. `*.SemanticModel` Ordner auswählen (z.B. `products/fabric/powerbi/dist/COM-001/COM-001.SemanticModel`)
4. View → TMDL View aktivieren
5. Measures in `tables/_Measures.tmdl` prüfen

**Troubleshooting:**

| Problem | Lösung |
|---------|--------|
| TMDL View nicht verfügbar | Power BI Desktop auf neueste Version updaten (TMDL GA seit Nov 2024) |
| Syntax Error beim Laden | `test_tmdl.ps1` ausführen für Details |
| Measure nicht sichtbar | Prüfe `ref table _Measures` in model.tmdl |
| Format String ignoriert | Prüfe Syntax: `formatString: "#,0.00"` (Quotes required) |

---

## Empfohlener Test-Workflow

### 1. Während der Entwicklung:
```powershell
# Quick Syntax Check (von Repo-Root)
./products/fabric/powerbi/tooling/test_tmdl.ps1 -TmdlFile "path\to\_Measures.tmdl"
```

### 2. Vor Commit:
```powershell
# Fabric-Checks (TMDL Syntax, DAX, Measures vs KPI)
./products/fabric/powerbi/tooling/run_fabric_checks.ps1

# Oder umfassend inkl. Stage 1
./tooling/run_all_checks.ps1
```

### 3. Beispiel: COM-001 (Sales Performance) testen
```powershell
# Schritt 1: Measures generieren
./tooling/generator/generate_tmdl_measures.ps1 -UseCase "COM-001" -OverwriteExisting

# Schritt 2: Syntax validieren
./products/fabric/powerbi/tooling/test_tmdl.ps1 -TmdlFile "products\fabric/powerbi\dist\COM-001\COM-001.SemanticModel\definition\tables\_Measures.tmdl"

# Schritt 3: Fabric-Checks
./products/fabric/powerbi/tooling/run_fabric_checks.ps1

# Schritt 4: In Power BI Desktop öffnen
explorer "products\fabric/powerbi\dist\COM-001"
# Dann: File → Open → COM-001.SemanticModel
```

---

## Referenzen

### Microsoft Official:
- TMDL Overview: <https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview>
- TMDL How-To: <https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-how-to>
- Power BI TMDL View: <https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-tmdl-view>
- VS Code Extension: <https://marketplace.visualstudio.com/items?itemName=analysis-services.TMDL>

### Internal (von Repo-Root):
- [TMDL Best Practices](../docs/tmdl_best_practices.md)
- [run_fabric_checks.ps1](run_fabric_checks.ps1) — TMDL Syntax, DAX, Measures vs KPI
- [core/kpi_catalog](../../../../core/kpi_catalog/KPI_Catalog.md)
