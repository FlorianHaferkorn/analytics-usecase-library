# Power BI MCP - Automated Self-Iterating Flow

## Vision: KPI Catalog → Semantic Model → Reports (Fully Automated)

**Ziel:** Von Use Case ID bis zum fertigen Report ohne manuelle Intervention - mit selbst-korrigierendem Feedback-Loop.

Technical TODOs for this flow are listed in [internal/technical_backlog.md](../../../../internal/technical_backlog.md) § Power BI MCP.

---

## 🎯 **End-to-End Flow Overview**

```mermaid
graph TB
    UC[Use Case ID] --> KPI[KPI Catalog Lookup]
    KPI --> TM[TMDL Measures Generate]
    TM --> SM[Semantic Model Ops via MCP]
    SM --> VAL[Validation & BPA]
    VAL -->|Pass| REL[Relationships Auto-Config]
    VAL -->|Fail| ITER[Self-Healing Iteration]
    ITER --> SM
    REL --> HIER[Hierarchies & Sort-By]
    HIER --> PER[Perspectives]
    PER --> DAX[DAX Validation]
    DAX -->|Pass| RPT[Report Generation]
    DAX -->|Fail| ITER
    RPT --> FINAL[Deploy & Test]
```

---

## 📦 **Phase 1: Setup & Connection (Einmalig)**

### 1.1 Power BI MCP Connection etablieren

**Prerequisites:**
- Power BI Desktop installiert (mit TMDL View Support)
- Analysis Services TMDL Extension für VS Code
- PBIP-Projekt im Git-Repo
- **Python 3.x** für Registry, page_scaffold_generator (Report-Erstellung mit Visuals). Auf Windows wird Python typischerweise über den **py-Launcher** aufgerufen (z. B. `py -3`); der Orchestrator verwendet `py -3`, `python3` oder `python` in dieser Reihenfolge. Ohne Python: Fallback auf report_generator.ps1 (nur Report-Struktur, keine UX-Engine).

**Connection Setup Script:**
```powershell
# products/fabric/powerbi/orchestrator/setup_connection.ps1

Param(
    [string]$WorkspaceRoot = "products/fabric/powerbi/dist",
    [string]$ModelName = "Commercial",
    [string]$ConnectionName = "local_pbip"
)

Write-Host "=== Power BI MCP Connection Setup ===" -ForegroundColor Cyan

# 1. Stelle sicher dass PBIP-Struktur existiert
$modelPath = Join-Path $WorkspaceRoot "$ModelName.SemanticModel"
if (-not (Test-Path $modelPath)) {
    Write-Host "Creating PBIP structure..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "$modelPath\definition\tables" -Force | Out-Null
    New-Item -ItemType Directory -Path "$modelPath\definition\relationships" -Force | Out-Null
    
    # model.tmdl erstellen
    @"
model Model
  culture: de-DE
  defaultPowerBIDataSourceVersion: PowerBI_V3

"@ | Out-File -Encoding UTF8NoBOM "$modelPath\definition\model.tmdl"
    
    # .platform erstellen
    @"
{
  "`$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
  "metadata": {
    "type": "SemanticModel",
    "displayName": "$ModelName"
  },
  "config": {
    "version": "2.0",
    "logicalId": "$(New-Guid)"
  }
}
"@ | Out-File -Encoding UTF8NoBOM "$modelPath\.platform"
}

Write-Host "✓ PBIP structure ready: $modelPath" -ForegroundColor Green

# 2. Connection Details ausgeben
Write-Host "`nPower BI MCP Connection Details:" -ForegroundColor Cyan
Write-Host "  Connection Name: $ConnectionName" -ForegroundColor Gray
Write-Host "  Model Path:      $modelPath" -ForegroundColor Gray
Write-Host "  Definition Path: $modelPath\definition" -ForegroundColor Gray

# 3. Connection-Datei erstellen
$connFile = "products/fabric/powerbi/orchestrator/connections.json"
$conn = @{
    $ConnectionName = @{
        modelPath = $modelPath
        definitionPath = "$modelPath\definition"
        lastUsed = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    }
}
$conn | ConvertTo-Json -Depth 5 | Out-File -Encoding UTF8NoBOM $connFile

Write-Host "`n✓ Connection saved: $connFile" -ForegroundColor Green
Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Run: .\products\fabric/powerbi\orchestrator\orchestrate_full_model.ps1 -UseCase 'COM-001'" -ForegroundColor Gray
```

---

## 🔄 **Phase 2: Orchestration - Self-Iterating Flow**

### 2.1 Master Orchestrator

**File:** `products/fabric/powerbi/orchestrator/orchestrate_full_model.ps1`

```powershell
Param(
    [Parameter(Mandatory=$true)][string]$UseCase,
    [string]$ConnectionName = "local_pbip",
    [int]$MaxIterations = 5,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Power BI MCP - Full Model Orchestration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Use Case:     $UseCase" -ForegroundColor Gray
Write-Host "Connection:   $ConnectionName" -ForegroundColor Gray
Write-Host "Max Iterations: $MaxIterations" -ForegroundColor Gray
Write-Host ""

# State Tracking
$state = @{
    useCase = $UseCase
    iteration = 0
    phase = "init"
    errors = @()
    warnings = @()
    completed = @()
}

function Log-Phase {
    param([string]$Phase, [string]$Status = "START")
    $color = switch($Status) {
        "START" { "Cyan" }
        "PASS" { "Green" }
        "WARN" { "Yellow" }
        "FAIL" { "Red" }
    }
    Write-Host "[$($state.iteration)] $Phase - $Status" -ForegroundColor $color
}

function Invoke-WithRetry {
    param(
        [string]$PhaseName,
        [scriptblock]$Script,
        [int]$MaxRetries = 3
    )
    
    for ($i = 0; $i -lt $MaxRetries; $i++) {
        try {
            Log-Phase $PhaseName "START"
            & $Script
            Log-Phase $PhaseName "PASS"
            $state.completed += $PhaseName
            return $true
        } catch {
            $state.errors += @{
                phase = $PhaseName
                iteration = $state.iteration
                error = $_.Exception.Message
            }
            Log-Phase $PhaseName "FAIL"
            Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
            
            if ($i -lt ($MaxRetries - 1)) {
                Write-Host "  Retrying ($($i+1)/$MaxRetries)..." -ForegroundColor Yellow
                Start-Sleep -Seconds 2
            }
        }
    }
    return $false
}

# ===========================================
# PHASE 1: DATA FOUNDATION
# ===========================================
$state.phase = "data_foundation"
$state.iteration = 1

Invoke-WithRetry "Check Aurora Data" {
    $dataPath = "showcases\aurora_group\data\gold"
    if (-not (Test-Path $dataPath)) {
        throw "Aurora data not found at $dataPath"
    }
    $dims = @("dim_date", "dim_org", "dim_product", "dim_customer", "dim_promo", "dim_account")
    $facts = @("fact_sales", "fact_sales_budget", "fact_action_log", "fact_gl_journal")
    
    foreach ($dim in $dims) {
        if (-not (Test-Path "$dataPath\dimensions\$dim")) {
            throw "Missing dimension: $dim"
        }
    }
    foreach ($fact in $facts) {
        if (-not (Test-Path "$dataPath\facts\$fact")) {
            throw "Missing fact: $fact"
        }
    }
    Write-Host "  ✓ All required tables present" -ForegroundColor Green
}

# ===========================================
# PHASE 2: KPI CATALOG & MEASURE GENERATION
# ===========================================
$state.phase = "measure_generation"
$state.iteration = 2

Invoke-WithRetry "Generate TMDL Measures" {
    $result = & ./tooling/generator/generate_tmdl_measures.ps1 `
        -UseCase $UseCase `
        -UseCasesRoot "core/usecases/core" `
        -KpiCatalogRoot "core/kpi_catalog" `
        -DistRoot "products/fabric/powerbi/dist" `
        -OverwriteExisting
    
    if ($LASTEXITCODE -ne 0) {
        throw "Measure generation failed with exit code $LASTEXITCODE"
    }
    Write-Host "  ✓ Measures generated" -ForegroundColor Green
}

Invoke-WithRetry "Validate TMDL Syntax" {
    $tmdlFile = "dist\$UseCase\$UseCase.SemanticModel\definition\tables\_Measures.tmdl"
    $result = & ./products/fabric/powerbi/tooling/test_tmdl.ps1 -TmdlFile $tmdlFile
    
    if ($LASTEXITCODE -ne 0) {
        throw "TMDL validation failed"
    }
    Write-Host "  ✓ TMDL syntax valid" -ForegroundColor Green
}

# ===========================================
# PHASE 3: SEMANTIC MODEL OPERATIONS (MCP)
# ===========================================
$state.phase = "semantic_model_build"
$state.iteration = 3

# 3.1 Create Tables from Data Contracts → table_ops.ps1 -Operation CreateFromContract (or ExportFromContract for JSON)
#     orchestrate_full_model.ps1 calls table_ops.ps1 per required table; payload written to products/fabric/powerbi/orchestrator/out/table_ops_<UseCase>.json
# 3.2b Sync model.tmdl refs → ensure ref table X for every table in definition/tables/
# 3.3 Create Relationships (per domain, reproducible): relationship_ops.ps1 -Operation CreateFromBracket with first use case bracket; if 0 relationships, AutoDetect + write TMDL to definition/relationships/*.tmdl. See tmdl_best_practices.md and README.md.
# 3.4 Create Hierarchies Definition → hierarchy_ops.ps1 -Operation FromBracket -BracketPath <path> -OutJsonPath out/hierarchy_ops_<UseCase>.json
# 3.5 Write Hierarchies to TMDL → hierarchy_ops.ps1 -Operation WriteToTmdl per domain
# 3.6 Write diagram layout → write_diagram_layout.ps1 per domain; outputs diagramLayout.json (Model View, spaghetti principle). See tmdl_best_practices.md §10.

# ===========================================
# PHASE 4: VALIDATION & SELF-HEALING
# ===========================================
$state.phase = "validation"
$state.iteration = 4

$validationPassed = $false
$iterationCount = 0

while (-not $validationPassed -and $iterationCount -lt $MaxIterations) {
    $iterationCount++
    Write-Host "`n=== Validation Iteration $iterationCount ===" -ForegroundColor Cyan
    
    # Run BPA
    $bpaResult = Invoke-WithRetry "Run BPA Checks" {
        $bpaOutput = & ./tooling/run_all_checks.ps1 2>&1
        
        # Parse BPA output for errors
        $errors = $bpaOutput | Select-String -Pattern "ERROR|FAIL" -AllMatches
        
        if ($errors.Count -gt 0) {
            throw "BPA found $($errors.Count) errors"
        }
        Write-Host "  ✓ BPA checks passed" -ForegroundColor Green
    }
    
    if ($bpaResult) {
        $validationPassed = $true
    } else {
        Write-Host "  Analyzing errors for auto-correction..." -ForegroundColor Yellow
        
        # Self-Healing Logic
        foreach ($error in $state.errors | Where-Object { $_.iteration -eq $iterationCount }) {
            switch -Regex ($error.error) {
                "Missing formatString" {
                    Write-Host "  → Auto-fix: Adding default formatString" -ForegroundColor Yellow
                    # TODO: Update TMDL file with default format strings
                }
                "Missing displayFolder" {
                    Write-Host "  → Auto-fix: Adding default displayFolder" -ForegroundColor Yellow
                    # TODO: Update TMDL file with default folders
                }
                "Relationship cardinality" {
                    Write-Host "  → Auto-fix: Correcting relationship" -ForegroundColor Yellow
                    # TODO: Update relationship via MCP
                }
                default {
                    Write-Host "  → Manual intervention required: $($error.error)" -ForegroundColor Red
                }
            }
        }
        
        Start-Sleep -Seconds 2
    }
}

if (-not $validationPassed) {
    Write-Host "`n✗ Validation failed after $MaxIterations iterations" -ForegroundColor Red
    exit 1
}

# ===========================================
# PHASE 5: REPORT GENERATION (UX Engine)
# ===========================================
# Invoke-Phase5ReportGeneration (generate_phase5_reports.ps1)
# - Python: py -3 / python3 / python → generate_full_report.py (--use-case, --output, --dataset-reference, --repo-root)
#   Input: UseCase_Bracket.yaml ux_layout_rules, core/templates/page_templates/ (Slot_Definitions, Visual_to_Slot_Mapping).
#   Output: products\fabric\powerbi\dist\<UC>_<Title>.Report (definition/report.json, definition/pages/, definition.pbir).
#   datasetReference in definition.pbir (nicht in report.json; PBIP/Fabric 3.0). Pfad relativ zum Report, z. B. ..\Commercial.SemanticModel.
# - Basis-Theme: apply_report_theme.ps1 -SyncBaseTheme (Quelle tooling/report_quality/base_theme.py, D-587), je Report, mit und ohne Custom Theme.
# - Theme: theme_config.json (defaultThemeName) oder -ThemeName → apply_report_theme.ps1.
# - Ohne Python: Fallback report_generator.ps1 (nur Struktur, keine Visuals).
# ===========================================
# PHASE 6: VALIDATE FABRIC OUTPUT
# ===========================================
# run_fabric_checks.ps1, check_report_structure.ps1, validate_pbip.ps1, optional pbi-tools compile.

# FINAL SUMMARY – Output (Fabric dist)
#   Model:  products\fabric\powerbi\dist\<Domain>.SemanticModel
#   Report: products\fabric\powerbi\dist\<UC>_<Title>.Report  (datasetReference → Domain-Modell im selben dist)
# Next: Open model/report in Desktop, validate, deploy (deploy.ps1).
```

### 2.2 Phase 5: Report Generation – UX Engine im Detail

Phase 5 nutzt dieselbe **Builder-Engine** wie manuelle Report-Erstellung: `generate_full_report.py` → `PageScaffoldGenerator` → `ConfigLoader` + `PageBuilder`. Es gibt keinen separaten Automation-Pfad; alle unten beschriebenen Features sind im Automation Flow aktiv.

**Eingaben (aus Bracket und Templates):**

| Quelle | Verwendung |
|--------|------------|
| **UseCase_Bracket.yaml** `ux_layout_rules` | `page_1_summary` (Overview), `page_2_execution` (Detail), `page_template` / `template_id`, `report_canvas` (width/height), `component_3s` / `component_30s` / `component_300s` |
| **Grid-Templates** `core/templates/page_templates/grid_templates/` | **Pulse** (Overview): KPI_Cards, Slicer_Date, Main_1, Main_2, Main_3. **Action Matrix** (Detail): Slicer_Pane, Smart_Narrative, Detail_Matrix, ActionPanel |
| **Slot-Bindung** | Optional `slot_id` in `component_30s` (Main_1, Main_2, Main_3) für explizite Zuordnung; sonst Heuristik aus `visual_type` (trend_line → trend, waterfall → variance, etc.) |
| **Detail-Seite** | `component_300s.evidence_columns` / `evidence_measures` → Detail_Matrix-Spalten/Measures (über KPI-Katalog zu Measure-Namen aufgelöst). `action_panel: true` + `orchestration.action_code_ids` → Action Panel |

**Action Codes (Phase 1 – nur informativ):**

- **Action Panel:** Inhalt wird zur Build-Zeit aus den Action-Code-YAMLs erzeugt (`get_action_panel_content`): Name, Owner, lesbare Trigger-Bedingung (aus `trigger.levels`), Impact (aus `impact` / `impact_valuation`), optional Schritte. Optional `payload_mode` (full/summary/minimal) aus `component_300s`. Anzeige als Textbox im Slot **ActionPanel** (Grid action_matrix); kein API-/Webhook-Aufruf.
- **Zeilenweise Action:** Für spätere Phase 2 ist vorgesehen, in der Detail_Matrix eine optionale Spalte „ActionCode“ / „Recommended Action“ zu nutzen, sobald das Semantic Model eine entsprechende Tabelle/Measure bereitstellt. Im Scaffold wird dafür aktuell keine zusätzliche Spalte erzeugt (siehe ActionPanel_Spec, Page_Spec_3_30_300).

**Delta-Update:**

- Wenn der Report bereits existiert (`definition/pages/pages.json` + mindestens eine Seite), führt Phase 5 **kein** Full Overwrite aus, sondern einen **Delta-Sync** (`report_sync`): Soll (aus Bracket + Templates) vs. Ist (PBIP-Reader). Aktionen: fehlende Seiten/Visuals hinzufügen, obsolete Visuals entfernen, Positionen aus Grid-Blueprint aktualisieren (`apply_page_layout`). `report.json` und `version.json` werden im Update-Modus nicht überschrieben. Manuelle Seiten (außer den zwei Bracket-Seiten) bleiben erhalten.
- `--force-full` erzwingt bei Bedarf wieder eine komplette Neuerstellung.

**Ausgabe:**

- **Pfad:** `products\fabric\powerbi\dist\<UseCaseFolderName>.Report` (z. B. `COM-001_Sales_Performance.Report`). Use-Case-Ordnername aus `core/usecases/core/<ID>_*`; kein Schreiben nach `internal/archive/` oder ad-hoc Pfade.
- Nach dem Schreiben: bei Bedarf StaticResources (BaseThemes) aus Sample kopieren, dann Theme über `apply_report_theme.ps1` (defaultThemeName aus `showcases/aurora_group/theme_config.json` oder `-ThemeName`).

---

## 🔧 **Phase 3: Power BI MCP Integration Layer**

### 3.1 Table Operations Wrapper

**File:** `products/fabric/powerbi/orchestrator/table_ops.ps1`

```powershell
Param(
    [ValidateSet("Create","Update","Delete","Get","List")]
    [string]$Operation,
    [string]$ConnectionName = "local_pbip",
    [hashtable]$TableDefinition
)

# Wrapper für mcp_powerbi-model_table_operations
# Konvertiert Data Contract YAML → TMDL Table Definition

function Convert-DataContractToTableDef {
    param($Contract)
    
    $tableDef = @{
        name = $Contract.name
        description = $Contract.description
        columns = @()
    }
    
    foreach ($col in $Contract.columns) {
        $tableDef.columns += @{
            name = $col.name
            dataType = $col.type  # int64, string, date, decimal, etc.
            description = $col.description
            isHidden = ($col.role -eq "key")
            formatString = if ($col.format) { $col.format } else { "" }
        }
    }
    
    return $tableDef
}

# Execute MCP Operation
$request = @{
    connectionName = $ConnectionName
    operation = $Operation.ToLower()
}

if ($TableDefinition) {
    $request.createDefinition = Convert-DataContractToTableDef $TableDefinition
}

# Call Power BI MCP
# mcp_powerbi-model_table_operations -request $request
```

### 3.2 Relationship Operations Wrapper

**File:** `products/fabric/powerbi/orchestrator/relationship_ops.ps1`

```powershell
# Auto-detect relationships from:
# 1. UseCase_Bracket.yaml + data contract references (explicit)
# 2. Foreign Key naming conventions (implicit)
# 3. Data Contract lineage (inferred)

function Get-RelationshipsFromBracket {
    param([string]$BracketPath)
    
    $content = Get-Content $BracketPath -Raw | ConvertFrom-Yaml
    $dataContractRef = $content.overrides.data_contract_ref
    
    if ($dataContractRef -and (Test-Path $dataContractRef)) {
        # Parse data contract for relationship definitions
        # Return array of relationship objects
    }
}

function Auto-DetectRelationships {
    param([array]$Tables)
    
    $relationships = @()
    
    # Heuristic 1: *Key columns
    foreach ($fact in ($Tables | Where-Object { $_.type -eq "fact" })) {
        foreach ($col in $fact.columns) {
            if ($col.name -match '^(.+)Key$') {
                $dimName = "dim_" + $matches[1].ToLower()
                $dim = $Tables | Where-Object { $_.name -eq $dimName }
                
                if ($dim) {
                    $relationships += @{
                        from = $fact.name
                        fromColumn = $col.name
                        to = $dim.name
                        toColumn = $col.name
                        cardinality = "ManyToOne"
                        crossFilteringBehavior = "single"
                    }
                }
            }
        }
    }
    
    return $relationships
}
```

### 3.3 Measure Operations Wrapper

**File:** `products/fabric/powerbi/orchestrator/measure_ops.ps1`

```powershell
# Import measures from TMDL into model via MCP
# Parse _Measures.tmdl → Extract measure blocks → Create via MCP

function Import-MeasuresFromTMDL {
    param(
        [string]$TmdlFile,
        [string]$ConnectionName
    )
    
    $content = Get-Content $TmdlFile -Raw
    
    # Parse measure blocks
    $pattern = '(?ms)///\s*(.+?)\s*measure\s+''([^'']+)''\s*=\s*(.+?)(?=\n\s*(?:///|measure|$))'
    $matches = [regex]::Matches($content, $pattern)
    
    foreach ($match in $matches) {
        $description = $match.Groups[1].Value.Trim()
        $name = $match.Groups[2].Value
        $expression = $match.Groups[3].Value.Trim()
        
        # Extract formatString, displayFolder from expression
        $formatMatch = [regex]::Match($expression, 'formatString:\s*"([^"]+)"')
        $folderMatch = [regex]::Match($expression, 'displayFolder:\s*"([^"]+)"')
        
        $measureDef = @{
            name = $name
            expression = $expression
            description = $description
            formatString = if ($formatMatch.Success) { $formatMatch.Groups[1].Value } else { "" }
            displayFolder = if ($folderMatch.Success) { $folderMatch.Groups[1].Value } else { "00_General" }
        }
        
        # Create via MCP
        # mcp_powerbi-model_measure_operations -Operation Create -MeasureDefinition $measureDef
    }
}
```

---

## 🎨 **Phase 4 (Orchestrator Phase 5): Report Generation – UX Engine**

**File:** `products/fabric/powerbi/orchestrator/generate_phase5_reports.ps1` (dot-sourced from `orchestrate_full_model.ps1`).

### Ablauf (Report-Erstellung)

1. **Python-Aufruf:** Der Orchestrator verwendet `py -3`, `python3` oder `python` (in dieser Reihenfolge). Unter Windows wird Python typischerweise über den **py-Launcher** ausgeführt (`py -3`).
2. **generate_full_report.py** (`products/fabric/powerbi/tooling/page_scaffold_generator/generate_full_report.py`):
   - Eingabe: Use Case ID, Bracket **ux_layout_rules**, **core/templates/page_templates/** (Slot_Definitions, Visual_to_Slot_Mapping, page_types T1–T4).
   - Ausgabe: `products/fabric/powerbi/dist/<UC>_<Title>.Report` (z. B. `COM-001_Sales_Performance.Report`) mit `definition/report.json`, `definition/pages/`, **definition.pbir**.
   - **datasetReference** wird in **definition.pbir** gesetzt (nicht in report.json; PBIP/Fabric 3.0). Relativer Pfad zum Domain-Modell im selben dist, z. B. `..\Commercial.SemanticModel` (über `Get-DatasetReferenceRelativeFromReport` in map_aurora_domains.ps1).
3. **Basis-Theme:** `apply_report_theme.ps1 -SyncBaseTheme` schreibt `StaticResources/SharedResources/BaseThemes/<name>.json` aus der vendorten Kopie in `tooling/report_quality/base_theme.py` und setzt `themeCollection.baseTheme` plus den SharedResources-Eintrag (D-587; einziger Bezugsweg, kein fester Theme-Name im Orchestrator). Läuft auch ohne Custom Theme.
4. **Theme:** Aus `showcases/aurora_group/theme_config.json` (`defaultThemeName`) oder Parameter `-ThemeName`; Anwendung via **apply_report_theme.ps1** (Theme aus `products/fabric/powerbi/themes/`, vendort aus Freelancing `products/pbi_theme`).
5. **Fallback:** Wenn kein Python gefunden wird → **report_generator.ps1** (nur Report-Struktur/Sections, keine Visuals).

### Validierung nach Report (Phase 6 im Orchestrator)

- **run_fabric_checks.ps1** (TMDL, PBIP readiness, diagram layout, measures vs KPI).
- **check_report_structure.ps1** (report.json, datasetReference, Struktur).
- **validate_pbip.ps1** pro Report-PBIP-Ordner.
- Optional: **pbi-tools compile** pro Semantic Model und Report.

Siehe auch: [PBIP_REPORT_STRUCTURE.md](../docs/PBIP_REPORT_STRUCTURE.md), [orchestrator README](README.md).

---

## 🔄 **Phase 5: Self-Healing & Iteration Logic**

### 5.1 Error Pattern Recognition

```powershell
# products/fabric/powerbi/orchestrator/self_healing.ps1

$ErrorPatterns = @{
    # Pattern → Auto-Fix Function
    "Missing formatString for measure '(.+)'" = {
        param($MeasureName)
        # Determine type from KPI Catalog
        # Apply default format (EUR #,0.00 for amounts, 0.0% for rates)
    }
    
    "Relationship cardinality mismatch" = {
        # Check actual cardinalities in data
        # Update relationship definition
    }
    
    "Ambiguous relationship path" = {
        # Set one relationship to inactive
        # Document in model.tmdl
    }
    
    "Circular dependency in measure '(.+)'" = {
        # Analyze DAX dependency graph
        # Suggest refactoring
    }
}

function Invoke-SelfHealing {
    param([array]$Errors)
    
    $fixed = 0
    
    foreach ($error in $Errors) {
        foreach ($pattern in $ErrorPatterns.Keys) {
            $match = [regex]::Match($error.message, $pattern)
            if ($match.Success) {
                Write-Host "Auto-fixing: $($error.message)" -ForegroundColor Yellow
                & $ErrorPatterns[$pattern] $match.Groups[1].Value
                $fixed++
                break
            }
        }
    }
    
    return $fixed
}
```

### 5.2 Quality Gates

```powershell
$QualityGates = @(
    @{
        name = "TMDL Syntax Valid"
        check = { Test-TmdlSyntax }
        blocker = $true
    },
    @{
        name = "All Measures Have Format Strings"
        check = { Test-MeasureFormatStrings }
        blocker = $false  # Can auto-fix
    },
    @{
        name = "No Circular Dependencies"
        check = { Test-DAXDependencies }
        blocker = $true
    },
    @{
        name = "All Relationships Single-Direction"
        check = { Test-Relationships }
        blocker = $false
    },
    @{
        name = "BPA Rules Passed"
        check = { Invoke-BPA }
        blocker = $false
    }
)

function Test-QualityGates {
    $results = @()
    
    foreach ($gate in $QualityGates) {
        $passed = & $gate.check
        $results += @{
            name = $gate.name
            passed = $passed
            blocker = $gate.blocker
        }
    }
    
    return $results
}
```

---

## 📊 **Phase 6: Deployment & Monitoring**

### 6.1 Deployment Pipeline

**Scripts:** `products/fabric/powerbi/orchestrator/deploy_gate.ps1`, `products/fabric/powerbi/orchestrator/deploy.ps1`

- **deploy_gate.ps1** (Zero-Tolerance): Runs `check_validate_data_contracts.ps1` and `check_registry_builder.ps1`; reads `master_registry.json` and fails if `failed_data_contracts` is non-empty. Call before any deploy; `deploy.ps1` invokes it at start.
- **deploy.ps1**: (1) Runs deploy_gate; (2) Workspace create/get (Fabric REST or Power BI groups API); (3) Semantic Model import; (4) Report publish and bind; (5) Refresh schedule (optional); (6) Security/RLS (optional). Use `-GateOnly` to only run the gate.

**Configuration (env vars; do not commit secrets):** `FABRIC_TENANT_ID`, `FABRIC_CLIENT_ID`, `FABRIC_CLIENT_SECRET` (or PBI_* equivalents); `FABRIC_WORKSPACE_NAME` or `FABRIC_WORKSPACE_ID`.

**Fabric REST (stubs in deploy.ps1):** Workspace (GET/POST groups), Semantic Model import (PBIP/dataset API), Report import/bind, Refresh schedule, RLS/security mapping. Add auth (e.g. client credentials) and API calls as needed; required permissions: workspace admin, dataset create/update, report deploy.

### 6.2 Monitoring Dashboard

```powershell
# Track orchestration metrics
$metrics = @{
    totalRuns = 0
    successRate = 0.0
    avgIterations = 0.0
    autoFixRate = 0.0
    useCaseCoverage = @{}
}

# Log to metrics database
# Visualize in monitoring dashboard
```

---

## 🚀 **Quick Start: End-to-End Example**

```powershell
# 1. Setup (einmalig)
./products/fabric/powerbi/orchestrator/setup_connection.ps1 `
    -WorkspaceRoot "products/fabric/powerbi/dist" `
    -ModelName "Commercial"

# 2. Generate COM-001 (Sales Performance) komplett
./products/fabric/powerbi/orchestrator/orchestrate_full_model.ps1 `
    -UseCase "COM-001" `
    -MaxIterations 5

# 3. Öffne in Power BI Desktop
explorer "showcases\aurora_group\semantic_models\Commercial.SemanticModel"

# 4. Deploy to Fabric
./products/fabric/powerbi/orchestrator/deploy.ps1 `
    -WorkspaceName "DM_ActionReady" `
    -ModelPath "showcases\aurora_group\semantic_models\Commercial.SemanticModel"
```

---

## 📈 **Success Metrics**

| Metric | Target | Measurement |
|--------|--------|-------------|
| Automation Rate | >90% | Manual interventions / Total steps |
| First-Run Success | >80% | Successful runs without iteration |
| Self-Healing Rate | >70% | Auto-fixed errors / Total errors |
| Time to Report | <15 min | From Use Case ID to published report |
| Quality Score | >95% | BPA checks passed |

---

## 🔮 **Future Enhancements**

1. **AI-Driven DAX Optimization:** Use GPT-4 to optimize complex measures
2. **Visual Recommendation Engine:** Suggest best visual types per KPI
3. **Anomaly Detection:** Auto-flag suspicious data patterns
4. **Natural Language Report Builder:** "Create sales report for Q4" → Full report
5. **Cross-Use-Case Reuse:** Automatically detect similar measures across models

---

**Status:** Ready for Implementation  
**Dependencies:** Power BI MCP Server, TMDL Tools, KPI Catalog, Data Contracts  
**Owner:** Analytics Engineering Team  
**Last Updated:** 02.02.2026
