# tooling/powerbi_mcp/orchestrate_full_model.ps1
# Domain-aware Semantic Model Orchestrator
# Single source: Use-Case-Root (default core/usecases/core). Modes: -UseCase (one), -Domain (all in domain), -All (all).

Param(
    [Parameter(Mandatory=$false)][string]$UseCase,
    [Parameter(Mandatory=$false)][string]$Domain,
    [Parameter(Mandatory=$false)][switch]$All,
    [string]$UseCaseRoot = "core\usecases\core",
    [string]$ConnectionName = "local_pbip",
    [int]$MaxIterations = 5,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Path Resolution - Calculate before changing location (repo = parent of tooling)
$script:ToolsRoot = Split-Path -Parent $PSScriptRoot
$script:RepoRoot = Split-Path -Parent $script:ToolsRoot
Push-Location $script:RepoRoot

# Aurora domain semantic models: central mapping (prefix <-> domain name <-> model path, data contract)
. "$PSScriptRoot\AuroraDomainMapping.ps1"

# Validate: exactly one of -UseCase, -Domain, -All
$modeCount = 0
if ($UseCase) { $modeCount++ }
if ($Domain) { $modeCount++ }
if ($All) { $modeCount++ }
if ($modeCount -eq 0) {
    throw "Specify exactly one of: -UseCase <id>, -Domain <name>, -All"
}
if ($modeCount -gt 1) {
    throw "Specify only one of: -UseCase, -Domain, -All (not multiple)"
}

function Get-UseCaseIdsFromRoot {
    param([string]$Root)
    $absRoot = if ([System.IO.Path]::IsPathRooted($Root)) { $Root } else { Join-Path $script:RepoRoot $Root }
    if (-not (Test-Path $absRoot)) {
        return @()
    }
    $ids = @()
    Get-ChildItem $absRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $name = $_.Name
        if ($name -match '^([A-Z]{2,3}-\d+)_') {
            $id = $Matches[1]
            $bracketPath = Join-Path $_.FullName "UseCase_Bracket.yaml"
            if (Test-Path $bracketPath) {
                $ids += $id
            }
        }
    }
    return $ids | Sort-Object -Unique
}

# Domain name -> prefix mapping
function Get-DomainPrefix {
    param([string]$DomainName)
    switch ($DomainName.ToUpper()) {
        "COMMERCIAL" { return "COM" }
        "FINANCE" { return "FIN" }
        "OPERATIONS" { return "OPS" }
        "SUPPLYCHAIN" { return "SCM" }
        "EXPERIENCE" { return "XD" }
        default { return $DomainName.Substring(0, [Math]::Min(3, $DomainName.Length)).ToUpper() }
    }
}

# Resolve scope once: $script:SelectedUseCaseIds (array of IDs)
$allIdsFromRoot = Get-UseCaseIdsFromRoot -Root $UseCaseRoot
if ($All) {
    $script:SelectedUseCaseIds = @($allIdsFromRoot)
    $scopeType = "All"
    $scopeName = "All"
} elseif ($Domain) {
    $prefix = Get-DomainPrefix -DomainName $Domain
    $script:SelectedUseCaseIds = @($allIdsFromRoot | Where-Object { $_ -like "$prefix-*" })
    if ($script:SelectedUseCaseIds.Count -eq 0) {
        throw "No use cases found for domain: $Domain (prefix: $prefix) in $UseCaseRoot"
    }
    $scopeType = "Domain"
    $scopeName = $Domain
} else {
    # -UseCase: single ID; must exist in root
    $script:SelectedUseCaseIds = @($allIdsFromRoot | Where-Object { $_ -eq $UseCase })
    if ($script:SelectedUseCaseIds.Count -eq 0) {
        throw "Use case '$UseCase' not found in $UseCaseRoot (must exist as folder <ID>_Title with UseCase_Bracket.yaml)"
    }
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

# PHASE 2: MEASURE GENERATION (per-domain Aurora semantic models)
$state.phase = "measure_generation"
$state.iteration = 2
$state.domainMeasurePaths = @()

$byDomain = Get-UseCaseIdsGroupedByDomain -UseCaseIds $script:SelectedUseCaseIds
$ucRootForScript = $UseCaseRoot -replace '\\', '/'
Invoke-WithRetry "Generate Measures (Aurora per domain)" {
    foreach ($domainName in $byDomain.Keys) {
        $ucIds = $byDomain[$domainName]
        $tablesPath = Get-AuroraDomainTablesPath -DomainName $domainName
        if (-not $tablesPath) {
            Write-Host "  WARNING: No Aurora model path for domain $domainName, skipping" -ForegroundColor Yellow
            continue
        }
        $modelPath = Get-AuroraDomainModelPath -DomainName $domainName
        $defPath = Join-Path $script:RepoRoot "$modelPath\definition"
        if (-not (Test-Path $defPath)) {
            New-Item -ItemType Directory -Path (Join-Path $script:RepoRoot "$tablesPath") -Force | Out-Null
            $modelContent = "model Model`r`n  culture: de-DE`r`n  defaultPowerBIDataSourceVersion: PowerBI_V3`r`n`r`n"
            $utf8 = New-Object System.Text.UTF8Encoding $false
            [System.IO.File]::WriteAllText((Join-Path $script:RepoRoot "$modelPath\definition\model.tmdl"), $modelContent, $utf8)
        }
        Write-Host "  Domain $domainName : $($ucIds -join ', ')" -ForegroundColor Gray
        & ./tooling/generation/generate_tmdl_measures.ps1 `
            -UseCase $ucIds `
            -UseCasesRoot $ucRootForScript `
            -KpiCatalogRoot "core/kpi_catalog" `
            -DistRoot "products/fabric_powerbi/dist" `
            -TargetTablesDir $tablesPath `
            -OverwriteExisting | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Measure generation failed for domain $domainName (exit $LASTEXITCODE)"
        }
        $measuresPath = Join-Path $script:RepoRoot "$tablesPath\_Measures.tmdl"
        if (-not (Test-Path $measuresPath)) {
            throw "Aurora measures file not created: $measuresPath"
        }
        $state.domainMeasurePaths += $measuresPath
        $content = Get-Content $measuresPath -Raw
        $measureCount = ([regex]::Matches($content, "(?m)^\s*measure\s+")).Count
        Write-Host "  $domainName : $measureCount measures" -ForegroundColor Green
    }
    $state.measuresFile = if ($state.domainMeasurePaths.Count -gt 0) { $state.domainMeasurePaths[0] } else { $null }
}

Invoke-WithRetry "Validate TMDL Syntax" {
    if (-not (Test-Path ./products/fabric_powerbi/tooling/test_tmdl.ps1)) {
        Write-Host "  test_tmdl.ps1 not found, skipping" -ForegroundColor Yellow
        return
    }
    foreach ($mp in $state.domainMeasurePaths) {
        & ./products/fabric_powerbi/tooling/test_tmdl.ps1 -TmdlFile $mp | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "TMDL validation failed for $mp"
        }
    }
    Write-Host "  TMDL syntax valid (all domain models)" -ForegroundColor Green
}

# PHASE 3: SEMANTIC MODEL BUILD (per domain: tables from gold contract, relationships, hierarchies)
$state.phase = "semantic_model_build"
$state.iteration = 3

# 3.1 Measures already written per domain in Phase 2; no copy step.

# 3.2 Create Tables from Data Contracts (per domain, from gold)
Invoke-WithRetry "Create Tables from Contracts (per domain)" {
    $outDir = Join-Path $script:RepoRoot "tooling\powerbi_mcp\out"
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    foreach ($domainName in $byDomain.Keys) {
        $modelPath = Get-AuroraDomainModelPath -DomainName $domainName
        $goldContract = Get-AuroraDomainDataContract -DomainName $domainName
        $targetDir = Join-Path $script:RepoRoot (Get-AuroraDomainTablesPath -DomainName $domainName)
        if (-not $goldContract -or -not (Test-Path (Join-Path $script:RepoRoot $goldContract))) {
            Write-Host "  WARNING: Data contract not found for $domainName : $goldContract" -ForegroundColor Yellow
            continue
        }
        $requiredTables = Get-AuroraDomainRequiredTables -DomainName $domainName
        $createdTables = 0
        foreach ($tableName in $requiredTables) {
            $tmdlPath = Join-Path $targetDir "$tableName.tmdl"
            if (Test-Path $tmdlPath) {
                Write-Host "  [$domainName] Table exists: $tableName" -ForegroundColor Gray
                continue
            }
            try {
                $domainDefPath = Join-Path $script:RepoRoot "$modelPath\definition"
                & ./tooling/powerbi_mcp/table_ops.ps1 `
                    -Operation "CreateFromContract" `
                    -DataContractPath (Join-Path $script:RepoRoot $goldContract) `
                    -TableName $tableName `
                    -DefinitionPath $domainDefPath `
                    -ErrorAction Stop | Out-Null
                $createdTables++
                Write-Host "  [$domainName] Created table: $tableName" -ForegroundColor Green
            } catch {
                Write-Host "  WARNING: [$domainName] Could not create table $tableName : $_" -ForegroundColor Yellow
            }
        }
        Write-Host "  [$domainName] Tables created: $createdTables/$($requiredTables.Count)" -ForegroundColor Green
        $firstUc = $byDomain[$domainName][0]
        if ($firstUc) {
            try {
                & ./tooling/powerbi_mcp/table_ops.ps1 -Operation "ExportFromContract" -DataContractPath $goldContract -UseCase $firstUc -OutJsonPath (Join-Path $outDir "table_ops_$firstUc.json") -ErrorAction Stop | Out-Null
            } catch {
                Write-Host "  (ExportFromContract optional: $_)" -ForegroundColor DarkGray
            }
        }
    }
}

# 3.3 Create Relationships from UseCase_Bracket.yaml (using $script:SelectedUseCaseIds)
Invoke-WithRetry "Create Relationships" {
    $absRoot = if ([System.IO.Path]::IsPathRooted($UseCaseRoot)) { $UseCaseRoot } else { Join-Path $script:RepoRoot $UseCaseRoot }
    $bracketDirs = @()
    foreach ($ucId in $script:SelectedUseCaseIds) {
        $dir = Get-ChildItem $absRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "${ucId}_*" } | Select-Object -First 1
        if ($dir -and (Test-Path "$($dir.FullName)\UseCase_Bracket.yaml")) { $bracketDirs += $dir }
    }
    if ($bracketDirs.Count -eq 0) {
        Write-Host "  WARNING: No use case directory found for selected IDs" -ForegroundColor Yellow
        return
    }
    $outDir = Join-Path $script:RepoRoot "tooling\powerbi_mcp\out"
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    $created = 0
    foreach ($useCaseDir in $bracketDirs) {
        $bracketPath = "$($useCaseDir.FullName)\UseCase_Bracket.yaml"
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

# 3.4 User hierarchies from bracket + contract (using $script:SelectedUseCaseIds)
Invoke-WithRetry "Create Hierarchies Definition" {
    $absRoot = if ([System.IO.Path]::IsPathRooted($UseCaseRoot)) { $UseCaseRoot } else { Join-Path $script:RepoRoot $UseCaseRoot }
    $bracketDirs = @()
    foreach ($ucId in $script:SelectedUseCaseIds) {
        $dir = Get-ChildItem $absRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "${ucId}_*" } | Select-Object -First 1
        if ($dir -and (Test-Path "$($dir.FullName)\UseCase_Bracket.yaml")) { $bracketDirs += $dir }
    }
    if ($bracketDirs.Count -eq 0) {
        Write-Host "  WARNING: No use case directory found for selected IDs" -ForegroundColor Yellow
        return
    }
    $outDir = Join-Path $script:RepoRoot "tooling\powerbi_mcp\out"
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    $created = 0
    foreach ($useCaseDir in $bracketDirs) {
        $bracketPath = "$($useCaseDir.FullName)\UseCase_Bracket.yaml"
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
    $validatorScript = Join-Path $script:ToolsRoot "validation\validate_tmdl.ps1"
    foreach ($domainName in $byDomain.Keys) {
        $tmdlPath = Join-Path $script:RepoRoot (Get-AuroraDomainModelPath -DomainName $domainName) "definition"
        if (-not (Test-Path $tmdlPath)) {
            Write-Host "  [$domainName] TMDL definition folder not found, skipping" -ForegroundColor Yellow
            continue
        }
        Write-Host "  Validating TMDL [$domainName]..." -ForegroundColor Gray
        & $validatorScript -TmdlPath $tmdlPath -AutoFix
        if ($LASTEXITCODE -ne 0) {
            throw "TMDL validation failed for $domainName. Check bpa-rules-tmdl.json for rule violations."
        }
    }
    Write-Host "  OK TMDL validation passed (all domain models)" -ForegroundColor Green
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
    $reportUseCases = @($script:SelectedUseCaseIds)
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
    $pyExe = ($pyCmd -split " ")[0]
    $pyExeArgs = @(($pyCmd -split " ")[1..999] | Where-Object { $_ })
    $scriptPath = Join-Path $script:RepoRoot "products\fabric_powerbi\tooling\page_scaffold_generator\generate_full_report.py"
    foreach ($ucId in $reportUseCases) {
        $domainName = Get-DomainNameFromUseCaseId -UcId $ucId
        $datasetRef = Get-DatasetReferenceRelativeFromReport -DomainName $domainName
        if (-not $datasetRef) { $datasetRef = "..\..\..\showcases\aurora_group\semantic_models\Commercial.SemanticModel" }
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
foreach ($domainName in $byDomain.Keys) {
    $outputModel = Get-AuroraDomainModelPath -DomainName $domainName
    Write-Host "  [$domainName] $outputModel" -ForegroundColor Gray
}
Write-Host "  Reports: products\fabric_powerbi\dist\<UC>.Report (datasetReference = domain semantic model)" -ForegroundColor Gray

Write-Host ([Environment]::NewLine + "Next Steps:") -ForegroundColor Yellow
Write-Host "  1. Open a domain model in Power BI Desktop (e.g. showcases\aurora_group\semantic_models\Commercial.SemanticModel)" -ForegroundColor Gray
Write-Host "  2. Open a report: products\fabric_powerbi\dist\<UC>.Report (references that UC's domain model)" -ForegroundColor Gray
Write-Host "  3. Use -Domain <name> or -All to build domain semantic models" -ForegroundColor Gray

# Export state
$stateFile = Join-Path $PSScriptRoot "last_run_state.json"
$stateJson = $state | ConvertTo-Json -Depth 5
$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($stateFile, $stateJson, $utf8)
Write-Host ([Environment]::NewLine + "State saved: $stateFile") -ForegroundColor Green

if ($state.errors.Count -gt 0) {
    exit 1
}
