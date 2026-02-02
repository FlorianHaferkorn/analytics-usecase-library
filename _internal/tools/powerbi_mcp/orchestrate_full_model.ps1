# _internal/tools/powerbi_mcp/orchestrate_full_model.ps1
# Domain-aware Semantic Model Orchestrator

Param(
    [Parameter(Mandatory=$false)][string]$UseCase,
    [Parameter(Mandatory=$false)][string]$Domain,
    [string]$ConnectionName = "local_pbip",
    [int]$MaxIterations = 5,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

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

# PHASE 1: DATA FOUNDATION
$state.phase = "data_foundation"
$state.iteration = 1

Invoke-WithRetry "Check Aurora Data" {
    $dataPath = "showcases\aurora_group\data\gold"
    if (-not (Test-Path $dataPath)) {
        throw "Aurora data not found at $dataPath"
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
        $ucDir = Get-ChildItem "usecases\core" -Directory | Where-Object { $_.Name -like "$scopeName*" } | Select-Object -First 1
        if (-not $ucDir) {
            throw "UseCase directory not found for: $scopeName"
        }
        Write-Host "  Found: $($ucDir.Name)" -ForegroundColor Gray
        
        # Pass UseCase ID (COM-001) to script, not full directory name
        & ./_internal/tools/generation/generate_tmdl_measures.ps1 `
            -UseCase $scopeName `
            -UseCasesRoot "usecases/core" `
            -KpiCatalogRoot "framework/kpi_catalog" `
            -DistRoot "dist" `
            -OverwriteExisting | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            throw "Measure generation failed with exit code $LASTEXITCODE"
        }
        
        # generate-Script uses UseCase ID (COM-001), not directory name (COM-001_Sales_Performance)
        $measuresFile = "dist\$scopeName\$scopeName.SemanticModel\definition\tables\_Measures.tmdl"
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
        
        $ucDirs = Get-ChildItem "usecases\core" -Directory | Where-Object { $_.Name -like "$domainPrefix-*" }
        if ($ucDirs.Count -eq 0) {
            throw "No Use Cases found for domain: $scopeName (prefix: $domainPrefix)"
        }
        Write-Host "  Found $($ucDirs.Count) Use Cases: $($ucDirs.Name -join ', ')" -ForegroundColor Gray
        
        $allMeasures = @()
        foreach ($ucDir in $ucDirs) {
            Write-Host "  Generating $($ucDir.Name)..." -ForegroundColor Gray
            
            & ./_internal/tools/generation/generate_tmdl_measures.ps1 `
                -UseCase $ucDir.Name `
                -UseCasesRoot "usecases/core" `
                -KpiCatalogRoot "framework/kpi_catalog" `
                -DistRoot "dist" `
                -OverwriteExisting | Out-Null
            
            $measuresFile = "dist\$($ucDir.Name)\$($ucDir.Name).SemanticModel\definition\tables\_Measures.tmdl"
            if (Test-Path $measuresFile) {
                $allMeasures += (Get-Content $measuresFile -Raw)
            }
        }
        
        # Combine all measures
        $combinedPath = "dist\_domain_$scopeName\_Measures.tmdl"
        New-Item -ItemType Directory -Path (Split-Path $combinedPath -Parent) -Force -ErrorAction SilentlyContinue | Out-Null
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($combinedPath, ($allMeasures -join "`r`n`r`n"), $utf8)
        
        $measureCount = ([regex]::Matches(($allMeasures -join ""), "(?m)^\s*measure\s+")).Count
        Write-Host "  Domain measures generated: $measureCount" -ForegroundColor Green
        $state.measuresFile = $combinedPath
    }
}

Invoke-WithRetry "Validate TMDL Syntax" {
    if (-not (Test-Path ./_internal/tools/tmp/test_tmdl.ps1)) {
        Write-Host "  test_tmdl.ps1 not found, skipping" -ForegroundColor Yellow
        return
    }
    & ./_internal/tools/tmp/test_tmdl.ps1 -TmdlFile $state.measuresFile | Out-Null
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
    $goldContract = "data_contracts\domains\commercial_sales.yaml"
    
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
            & ./_internal/tools/powerbi_mcp/table_ops.ps1 `
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
}

# 3.3 Create Relationships from Technical Factsheet
Invoke-WithRetry "Create Relationships" {
    $techFactsheet = Get-ChildItem "usecases\core" -Directory | 
        Where-Object { $_.Name -like "$scopeName*" } | 
        Select-Object -First 1
    
    if (-not $techFactsheet) {
        Write-Host "  WARNING: Technical Factsheet not found for $scopeName" -ForegroundColor Yellow
        return
    }
    
    $techFactsheetPath = "$($techFactsheet.FullName)\Technical_Factsheet.md"
    
    if (-not (Test-Path $techFactsheetPath)) {
        Write-Host "  WARNING: Technical Factsheet missing: $techFactsheetPath" -ForegroundColor Yellow
        return
    }
    
    try {
        & ./_internal/tools/powerbi_mcp/relationship_ops.ps1 `
            -Operation "CreateFromFactsheet" `
            -ConnectionName "local_pbip" `
            -FactsheetPath $techFactsheetPath `
            -ErrorAction Stop | Out-Null
        
        Write-Host "  Relationships created from factsheet" -ForegroundColor Green
    } catch {
        Write-Host "  WARNING: Could not create relationships: $_" -ForegroundColor Yellow
    }
}

# PHASE 4: VALIDATION
$state.phase = "validation"
$state.iteration = 4

Invoke-WithRetry "Run Quality Checks" {
    if (-not (Test-Path ./_internal/tools/run_all_checks.ps1)) {
        Write-Host "  run_all_checks.ps1 not found, skipping" -ForegroundColor Yellow
        return
    }
    
    $bpaOutput = & ./_internal/tools/run_all_checks.ps1 2>&1 | Out-String
    $errorLines = $bpaOutput -split "`n" | Where-Object { $_ -match "ERROR|FAIL" }
    
    if ($errorLines.Count -gt 0) {
        Write-Host "  Found $($errorLines.Count) warnings" -ForegroundColor Yellow
        $state.warnings += "Quality checks: $($errorLines.Count) warnings"
    }
    Write-Host "  Quality checks completed" -ForegroundColor Green
}

# FINAL SUMMARY
$elapsed = ((Get-Date) - $state.startTime).TotalSeconds

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Model Orchestration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Scope:         $scopeType - $scopeName" -ForegroundColor Gray
Write-Host "Total Time:    $([int]$elapsed)s" -ForegroundColor Gray
Write-Host "Completed:     $($state.completed.Count) phases" -ForegroundColor Gray
Write-Host "Warnings:      $($state.warnings.Count)" -ForegroundColor Gray
Write-Host "Errors:        $($state.errors.Count)" -ForegroundColor Gray

if ($state.errors.Count -gt 0) {
    Write-Host "`nErrors:" -ForegroundColor Yellow
    $state.errors | ForEach-Object { Write-Host "  [$($_.phase)] $($_.error)" -ForegroundColor Gray }
}

Write-Host "`nOutput:" -ForegroundColor Cyan
$outputModel = "showcases\aurora_group\semantic_models\CoreActionReady.SemanticModel"
Write-Host "  Model:  $outputModel" -ForegroundColor Gray
Write-Host "  Measures: $outputModel\definition\tables\_Measures.tmdl" -ForegroundColor Gray

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Open in Power BI Desktop: explorer $outputModel" -ForegroundColor Gray
Write-Host "  2. Test with table_ops.ps1, relationship_ops.ps1, measure_ops.ps1" -ForegroundColor Gray
Write-Host "  3. Build complete domain model with -Domain Commercial" -ForegroundColor Gray

# Export state
$stateFile = "_internal\tools\powerbi_mcp\last_run_state.json"
$stateJson = $state | ConvertTo-Json -Depth 5
$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($stateFile, $stateJson, $utf8)
Write-Host "`nState saved: $stateFile" -ForegroundColor Green
