# tooling/powerbi_mcp/orchestrate_full_model.ps1
# Domain-aware Semantic Model Orchestrator

Param(
    [Parameter(Mandatory=$false)][string]$UseCase,
    [Parameter(Mandatory=$false)][string]$Domain,
    [string]$ConnectionName = "local_pbip",
    [int]$MaxIterations = 5,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Path Resolution - Calculate before changing location (repo = parent of tooling)
$script:ToolsRoot = Split-Path -Parent $PSScriptRoot
$script:RepoRoot = Split-Path -Parent $script:ToolsRoot
Push-Location $script:RepoRoot

# Validate input
if (-not $UseCase -and -not $Domain) {
    throw "Either -UseCase or -Domain must be specified"
}

# Determine scope
if ($Domain) {
    $scopeType = "Domain"
    $scopeName = $Domain
} else {
    $scopeType = "UseCase"
    $scopeName = $UseCase
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Power BI MCP - Model Orchestration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Scope:        $scopeType - $scopeName" -ForegroundColor Gray
Write-Host "Connection:   $ConnectionName" -ForegroundColor Gray
Write-Host ""

# State Tracking
$state = @{
    scopeType = $scopeType
    scopeName = $scopeName
    iteration = 0
    phase = "init"
    errors = @()
    warnings = @()
    completed = @()
    startTime = Get-Date
}

function Log-Phase {
    param([string]$Phase, [string]$Status = "START")
    $color = switch($Status) {
        "START" { "Cyan" }
        "PASS" { "Green" }
        "WARN" { "Yellow" }
        "FAIL" { "Red" }
    }
    $elapsed = ((Get-Date) - $state.startTime).TotalSeconds
    Write-Host "[$($state.iteration)] [$([int]$elapsed)s] $Phase - $Status" -ForegroundColor $color
}

function Invoke-WithRetry {
    param([string]$PhaseName, [scriptblock]$Script, [int]$MaxRetries = 3)
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

# PHASE 0: BUILD REGISTRY (required for Measure binding and Action Panel)
$state.phase = "registry"
$state.iteration = 0
Invoke-WithRetry "Build Registry" {
    $registryScript = Join-Path $script:RepoRoot "tooling\validation\check_registry_builder.ps1"
    if (-not (Test-Path $registryScript)) {
        throw "check_registry_builder.ps1 not found at $registryScript. Registry is required for build."
    }
    & $registryScript -Root $script:RepoRoot -FailOnError
    if ($LASTEXITCODE -ne 0) {
        throw "Registry build failed (exit $LASTEXITCODE). Fix contract/registry errors and retry."
    }
    $masterPath = Join-Path $script:RepoRoot "tooling\ontology\out\master_registry.json"
    if (-not (Test-Path $masterPath)) {
        throw "master_registry.json not found after registry build: $masterPath"
    }
    Write-Host "  Registry ready: $masterPath" -ForegroundColor Green
}

# PHASE 1: DATA FOUNDATION
$state.phase = "data_foundation"
$state.iteration = 1

Invoke-WithRetry "Check Aurora Data" {
    $dataPath = "showcases\aurora_group\data\gold"
    if (-not (Test-Path $dataPath)) {
        Write-Host "  WARNING: Aurora data not found at $dataPath (optional for measure/report build)" -ForegroundColor Yellow
        return
    }
    $dims = @("dim_date", "dim_org", "dim_product", "dim_customer", "dim_promo", "dim_account")
    $facts = @("fact_sales", "fact_sales_budget", "fact_action_log", "fact_gl_journal")
    
    $missing = @()
    foreach ($dim in $dims) {
        if (-not (Test-Path "$dataPath\dimensions\$dim")) { $missing += $dim }
    }
    foreach ($fact in $facts) {
        if (-not (Test-Path "$dataPath\facts\$fact")) { $missing += $fact }
    }
    if ($missing.Count -gt 0) {
        throw "Missing tables: $($missing -join ', ')"
    }
    $totalTables = $dims.Count + $facts.Count
    Write-Host "  All required tables present ($totalTables tables)" -ForegroundColor Green
}

# PHASE 2: MEASURE GENERATION
$state.phase = "measure_generation"
$state.iteration = 2

if ($scopeType -eq "UseCase") {
    Invoke-WithRetry "Generate UseCase Measures" {
        Write-Host "  UseCase: $scopeName" -ForegroundColor Gray
        
        # Find UseCase directory (format: COM-001_Sales_Performance)
        $ucDir = Get-ChildItem "core\usecases\core" -Directory | Where-Object { $_.Name -like "$scopeName*" } | Select-Object -First 1
        if (-not $ucDir) {
            throw "UseCase directory not found for: $scopeName"
        }
        Write-Host "  Found: $($ucDir.Name)" -ForegroundColor Gray
        
        # Pass UseCase ID (COM-001) to script, not full directory name
        & ./tooling/generation/generate_tmdl_measures.ps1 `
            -UseCase $scopeName `
            -UseCasesRoot "core/usecases/core" `
            -KpiCatalogRoot "core/kpi_catalog" `
            -DistRoot "products/fabric_powerbi/dist" `
            -OverwriteExisting | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            throw "Measure generation failed with exit code $LASTEXITCODE"
        }
        
        # generate-Script uses UseCase ID (COM-001), not directory name (COM-001_Sales_Performance)
        $measuresFile = "products\fabric_powerbi\dist\$scopeName\$scopeName.SemanticModel\definition\tables\_Measures.tmdl"
        if (-not (Test-Path $measuresFile)) {
            throw "Measures file not created"
        }
        
        $content = Get-Content $measuresFile -Raw
        $measureCount = ([regex]::Matches($content, "(?m)^\s*measure\s+")).Count
        Write-Host "  Measures generated: $measureCount" -ForegroundColor Green
        $state.measuresFile = $measuresFile
    }
} else {
    Invoke-WithRetry "Generate Domain Measures" {
        Write-Host "  Domain: $scopeName" -ForegroundColor Gray
        
        # Map domain to prefix
        $domainPrefix = switch ($scopeName.ToUpper()) {
            "COMMERCIAL" { "COM" }
            "FINANCE" { "FIN" }
            "OPERATIONS" { "OPS" }
            "SUPPLYCHAIN" { "SCM" }
            "EXPERIENCE" { "XD" }
            default { $scopeName.Substring(0, 3).ToUpper() }
        }
        
        $ucDirs = Get-ChildItem "core\usecases\core" -Directory | Where-Object { $_.Name -like "$domainPrefix-*" }
        if ($ucDirs.Count -eq 0) {
            throw "No Use Cases found for domain: $scopeName (prefix: $domainPrefix)"
        }
        Write-Host "  Found $($ucDirs.Count) Use Cases: $($ucDirs.Name -join ', ')" -ForegroundColor Gray
        
        $allMeasures = @()
        foreach ($ucDir in $ucDirs) {
            # Use Case ID (e.g. COM-001) for consistent paths and report output
            $ucId = ($ucDir.Name -split '_', 2)[0]
            Write-Host "  Generating $ucId ($($ucDir.Name))..." -ForegroundColor Gray
            
            & ./tooling/generation/generate_tmdl_measures.ps1 `
                -UseCase $ucId `
                -UseCasesRoot "core/usecases/core" `
                -KpiCatalogRoot "core/kpi_catalog" `
                -DistRoot "products/fabric_powerbi/dist" `
                -OverwriteExisting | Out-Null
            
            $measuresFile = "products\fabric_powerbi\dist\$ucId\$ucId.SemanticModel\definition\tables\_Measures.tmdl"
            if (Test-Path $measuresFile) {
                $allMeasures += (Get-Content $measuresFile -Raw)
            }
        }
        
        # Combine all measures
        $combinedPath = "products\fabric_powerbi\dist\_domain_$scopeName\_Measures.tmdl"
        New-Item -ItemType Directory -Path (Split-Path $combinedPath -Parent) -Force -ErrorAction SilentlyContinue | Out-Null
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($combinedPath, ($allMeasures -join "`r`n`r`n"), $utf8)
        
        $measureCount = ([regex]::Matches(($allMeasures -join ""), "(?m)^\s*measure\s+")).Count
        Write-Host "  Domain measures generated: $measureCount" -ForegroundColor Green
        $state.measuresFile = $combinedPath
    }
}

Invoke-WithRetry "Validate TMDL Syntax" {
    if (-not (Test-Path ./products/fabric_powerbi/tooling/test_tmdl.ps1)) {
        Write-Host "  test_tmdl.ps1 not found, skipping" -ForegroundColor Yellow
        return
    }
    & ./products/fabric_powerbi/tooling/test_tmdl.ps1 -TmdlFile $state.measuresFile | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "TMDL validation failed"
    }
    Write-Host "  TMDL syntax valid" -ForegroundColor Green
}

# PHASE 3: SEMANTIC MODEL BUILD
$state.phase = "semantic_model_build"
$state.iteration = 3

$targetModel = "showcases\aurora_group\semantic_models\CoreActionReady.SemanticModel"
$targetDir = "$targetModel\definition\tables"

# Ensure model structure exists
if (-not (Test-Path $targetModel)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    $modelContent = "model Model`r`n  culture: de-DE`r`n  defaultPowerBIDataSourceVersion: PowerBI_V3`r`n`r`n"
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText("$targetModel\definition\model.tmdl", $modelContent, $utf8)
}

# 3.1 Import Measures
Invoke-WithRetry "Import Measures to Model" {
    $targetFile = "$targetDir\_Measures.tmdl"
    Copy-Item $state.measuresFile $targetFile -Force
    Write-Host "  Measures imported to $targetFile" -ForegroundColor Green
}

# 3.2 Create Tables from Data Contracts (Aurora Gold Layer)
Invoke-WithRetry "Create Tables from Contracts" {
    $goldContract = "core\data_contracts\domains\commercial_sales.yaml"
    
    if (-not (Test-Path $goldContract)) {
        Write-Host "  WARNING: Data contract not found: $goldContract" -ForegroundColor Yellow
        Write-Host "  Skipping table creation (using stub mode)" -ForegroundColor Yellow
        return
    }
    
    # Required tables for COM-001
    $requiredTables = @("dim_date", "dim_org", "dim_product", "dim_customer", "fact_sales")
    $createdTables = 0
    
    foreach ($tableName in $requiredTables) {
        $tmdlPath = "$targetDir\$tableName.tmdl"
        
        if (Test-Path $tmdlPath) {
            Write-Host "  Table exists: $tableName" -ForegroundColor Gray
            continue
        }
        
        try {
            & ./tooling/powerbi_mcp/table_ops.ps1 `
                -Operation "CreateFromContract" `
                -ConnectionName "local_pbip" `
                -DataContractPath $goldContract `
                -TableName $tableName `
                -ErrorAction Stop | Out-Null
            
            $createdTables++
            Write-Host "  Created table: $tableName" -ForegroundColor Green
        } catch {
            Write-Host "  WARNING: Could not create table $tableName`: $_" -ForegroundColor Yellow
        }
    }
    
    Write-Host "  Tables created: $createdTables/$($requiredTables.Count)" -ForegroundColor Green
    $outDir = Join-Path $script:RepoRoot "tooling\powerbi_mcp\out"
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    try {
        & ./tooling/powerbi_mcp/table_ops.ps1 -Operation "ExportFromContract" -DataContractPath $goldContract -UseCase $scopeName -OutJsonPath (Join-Path $outDir "table_ops_$scopeName.json") -ErrorAction Stop | Out-Null
    } catch {
        Write-Host "  (ExportFromContract optional: $_)" -ForegroundColor DarkGray
    }
}

# 3.3 Create Relationships from UseCase_Bracket.yaml
Invoke-WithRetry "Create Relationships" {
    $bracketDirs = @()
    if ($scopeType -eq "Domain") {
        $domainPrefix = switch ($scopeName.ToUpper()) {
            "COMMERCIAL" { "COM" }; "FINANCE" { "FIN" }; "OPERATIONS" { "OPS" }; "SUPPLYCHAIN" { "SCM" }; "EXPERIENCE" { "XD" }
            default { $scopeName.Substring(0, 3).ToUpper() }
        }
        $bracketDirs = @(Get-ChildItem "core\usecases\core" -Directory | Where-Object { $_.Name -like "$domainPrefix-*" })
    } else {
        $one = Get-ChildItem "core\usecases\core" -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "$scopeName*" } | Select-Object -First 1
        if ($one) { $bracketDirs = @($one) }
    }
    if ($bracketDirs.Count -eq 0) {
        Write-Host "  WARNING: No use case directory found for scope $scopeName" -ForegroundColor Yellow
        return
    }
    $outDir = Join-Path $script:RepoRoot "tooling\powerbi_mcp\out"
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    $created = 0
    foreach ($useCaseDir in $bracketDirs) {
        $bracketPath = "$($useCaseDir.FullName)\UseCase_Bracket.yaml"
        if (-not (Test-Path $bracketPath)) {
            Write-Host "  WARNING: UseCase_Bracket.yaml missing: $bracketPath" -ForegroundColor Yellow
            continue
        }
        $ucId = ($useCaseDir.Name -split '_', 2)[0]
        $relJsonPath = Join-Path $outDir "relationship_ops_$ucId.json"
        try {
            & ./tooling/powerbi_mcp/relationship_ops.ps1 `
                -Operation "CreateFromBracket" `
                -ConnectionName "local_pbip" `
                -BracketPath $bracketPath `
                -OutJsonPath $relJsonPath `
                -ErrorAction Stop | Out-Null
            $created++
            Write-Host "  Relationships from $ucId" -ForegroundColor Green
        } catch {
            Write-Host "  WARNING: Could not create relationships for $ucId : $_" -ForegroundColor Yellow
        }
    }
    if ($created -gt 0) { Write-Host "  Relationships created for $created bracket(s)" -ForegroundColor Green }
}

# 3.4 User hierarchies from bracket + contract (output to out/ for MCP or doc)
Invoke-WithRetry "Create Hierarchies Definition" {
    $bracketDirs = @()
    if ($scopeType -eq "Domain") {
        $domainPrefix = switch ($scopeName.ToUpper()) {
            "COMMERCIAL" { "COM" }; "FINANCE" { "FIN" }; "OPERATIONS" { "OPS" }; "SUPPLYCHAIN" { "SCM" }; "EXPERIENCE" { "XD" }
            default { $scopeName.Substring(0, 3).ToUpper() }
        }
        $bracketDirs = @(Get-ChildItem "core\usecases\core" -Directory | Where-Object { $_.Name -like "$domainPrefix-*" })
    } else {
        $one = Get-ChildItem "core\usecases\core" -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "$scopeName*" } | Select-Object -First 1
        if ($one) { $bracketDirs = @($one) }
    }
    if ($bracketDirs.Count -eq 0) {
        Write-Host "  WARNING: No use case directory found for scope $scopeName" -ForegroundColor Yellow
        return
    }
    $outDir = Join-Path $script:RepoRoot "tooling\powerbi_mcp\out"
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    $created = 0
    foreach ($useCaseDir in $bracketDirs) {
        $bracketPath = "$($useCaseDir.FullName)\UseCase_Bracket.yaml"
        if (-not (Test-Path $bracketPath)) { continue }
        $ucId = ($useCaseDir.Name -split '_', 2)[0]
        $hierJsonPath = Join-Path $outDir "hierarchy_ops_$ucId.json"
        try {
            & ./tooling/powerbi_mcp/hierarchy_ops.ps1 `
                -Operation "FromBracket" `
                -BracketPath $bracketPath `
                -RepoRoot $script:RepoRoot `
                -OutJsonPath $hierJsonPath `
                -ErrorAction Stop | Out-Null
            $created++
            Write-Host "  Hierarchy definitions for $ucId" -ForegroundColor Green
        } catch {
            Write-Host "  WARNING: Hierarchy ops for $ucId : $_" -ForegroundColor Yellow
        }
    }
    if ($created -gt 0) { Write-Host "  Hierarchies written for $created bracket(s)" -ForegroundColor Green }
}

# PHASE 4: VALIDATION
$state.phase = "validation"
$state.iteration = 4

Invoke-WithRetry "Validate TMDL Syntax" {
    $tmdlPath = "showcases\aurora_group\semantic_models\CoreActionReady.SemanticModel\definition"
    
    if (-not (Test-Path $tmdlPath)) {
        Write-Host "  TMDL definition folder not found, skipping" -ForegroundColor Yellow
        return
    }
    
    Write-Host "  Validating TMDL files against bpa-rules-tmdl.json..." -ForegroundColor Gray
    
    $validatorScript = Join-Path $script:ToolsRoot "validation\validate_tmdl.ps1"
    
    & $validatorScript `
        -TmdlPath $tmdlPath `
        -AutoFix
    
    if ($LASTEXITCODE -ne 0) {
        throw "TMDL validation failed. Check bpa-rules-tmdl.json for rule violations."
    }
    
    Write-Host "  OK TMDL validation passed (auto-fixed where possible)" -ForegroundColor Green
}

Invoke-WithRetry "Run Quality Checks" {
    $checksScript = Join-Path $script:ToolsRoot "run_all_checks.ps1"
    
    if (-not (Test-Path $checksScript)) {
        Write-Host "  run_all_checks.ps1 not found, skipping" -ForegroundColor Yellow
        return
    }
    
    $bpaOutput = & $checksScript 2>&1 | Out-String
    $errorLines = $bpaOutput -split [Environment]::NewLine | Where-Object { $_ -match "ERROR|FAIL" }
    
    if ($errorLines.Count -gt 0) {
        Write-Host "  Found $($errorLines.Count) error/fail line(s)" -ForegroundColor Red
        $state.warnings += "Quality checks: $($errorLines.Count) errors"
        throw "Quality checks reported errors. Fix and run tooling\run_stage1_checks.ps1"
    }
    Write-Host "  Quality checks passed" -ForegroundColor Green
}

# PHASE 5: REPORT GENERATION (UX Engine: page_scaffold_generator, overview + detail, datasetReference)
$state.phase = "report_generation"
$state.iteration = 5
Invoke-WithRetry "Generate Report from Template" {
    $distReportRoot = Join-Path $script:RepoRoot "products\fabric_powerbi\dist"
    if (-not (Test-Path $distReportRoot)) { New-Item -ItemType Directory -Path $distReportRoot -Force | Out-Null }
    $reportUseCases = @()
    if ($scopeType -eq "Domain") {
        $domainPrefix = switch ($scopeName.ToUpper()) {
            "COMMERCIAL" { "COM" }; "FINANCE" { "FIN" }; "OPERATIONS" { "OPS" }; "SUPPLYCHAIN" { "SCM" }; "EXPERIENCE" { "XD" }
            default { $scopeName.Substring(0, 3).ToUpper() }
        }
        $reportUseCases = @(Get-ChildItem "core\usecases\core" -Directory | Where-Object { $_.Name -like "$domainPrefix-*" } | ForEach-Object { ($_.Name -split '_', 2)[0] })
    } else {
        $reportUseCases = @($scopeName)
    }
    $pyCmd = $null
    foreach ($cmd in @("py -3", "python3", "python")) {
        try {
            $parts = $cmd -split " "
            $exe = $parts[0]
            $exeArgs = @($parts[1..999] | Where-Object { $_ }) + @("--version")
            $ver = (& $exe $exeArgs 2>&1) -join " "
            if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3") { $pyCmd = $cmd; break }
        } catch { continue }
    }
    if (-not $pyCmd) {
        Write-Host "  WARNING: Python 3 not found; falling back to report_generator.ps1 (empty visuals)" -ForegroundColor Yellow
        foreach ($ucId in $reportUseCases) {
            & ./tooling/powerbi_mcp/report_generator.ps1 -UseCase $ucId -OutputPath $distReportRoot -ErrorAction Stop | Out-Null
            Write-Host "  Report structure created for $ucId (fallback)" -ForegroundColor Green
        }
        return
    }
    $datasetRef = "..\..\..\showcases\aurora_group\semantic_models\CoreActionReady.SemanticModel"
    $pyExe = ($pyCmd -split " ")[0]
    $pyExeArgs = @(($pyCmd -split " ")[1..999] | Where-Object { $_ })
    $scriptPath = Join-Path $script:RepoRoot "products\fabric_powerbi\tooling\page_scaffold_generator\generate_full_report.py"
    foreach ($ucId in $reportUseCases) {
        $reportFolder = Join-Path $distReportRoot "$ucId.Report"
        $allArgs = $pyExeArgs + @($scriptPath, "--use-case", $ucId, "--output", $reportFolder, "--repo-root", $script:RepoRoot, "--dataset-reference", $datasetRef)
        & $pyExe @allArgs 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "generate_full_report.py failed for $ucId (exit $LASTEXITCODE). Check Bracket ux_layout_rules and page_scaffold_generator."
        }
        Write-Host "  Report created for $ucId (overview + detail, UX Engine)" -ForegroundColor Green
    }
}

# FINAL SUMMARY
$elapsed = ((Get-Date) - $state.startTime).TotalSeconds

Write-Host ([Environment]::NewLine + "========================================") -ForegroundColor Green
Write-Host "Model Orchestration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Scope:         $scopeType - $scopeName" -ForegroundColor Gray
Write-Host "Total Time:    $([int]$elapsed)s" -ForegroundColor Gray
Write-Host "Completed:     $($state.completed.Count) phases" -ForegroundColor Gray
Write-Host "Warnings:      $($state.warnings.Count)" -ForegroundColor Gray
Write-Host "Errors:        $($state.errors.Count)" -ForegroundColor Gray

if ($state.errors.Count -gt 0) {
    Write-Host ([Environment]::NewLine + "Errors:") -ForegroundColor Yellow
    $state.errors | ForEach-Object { Write-Host "  [$($_.phase)] $($_.error)" -ForegroundColor Gray }
}

Write-Host ([Environment]::NewLine + "Output:") -ForegroundColor Cyan
$outputModel = "showcases\aurora_group\semantic_models\CoreActionReady.SemanticModel"
Write-Host "  Model:  $outputModel" -ForegroundColor Gray
Write-Host "  Measures: $outputModel\definition\tables\_Measures.tmdl" -ForegroundColor Gray

Write-Host ([Environment]::NewLine + "Next Steps:") -ForegroundColor Yellow
Write-Host "  1. Open in Power BI Desktop: explorer $outputModel" -ForegroundColor Gray
Write-Host "  2. Test with table_ops.ps1, relationship_ops.ps1, measure_ops.ps1" -ForegroundColor Gray
Write-Host "  3. Build complete domain model with -Domain Commercial" -ForegroundColor Gray

# Export state
$stateFile = Join-Path $PSScriptRoot "last_run_state.json"
$stateJson = $state | ConvertTo-Json -Depth 5
$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($stateFile, $stateJson, $utf8)
Write-Host ([Environment]::NewLine + "State saved: $stateFile") -ForegroundColor Green

if ($state.errors.Count -gt 0) {
    exit 1
}
