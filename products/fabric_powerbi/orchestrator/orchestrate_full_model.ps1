# products/fabric_powerbi/orchestrator/orchestrate_full_model.ps1
# Domain-aware Semantic Model Orchestrator
# Single source: Use-Case-Root (default core/usecases/core). Modes: -UseCase (one), -Domain (all in domain), -All (all).

Param(
    [Parameter(Mandatory=$false)][string]$UseCase,
    [Parameter(Mandatory=$false)][string]$Domain,
    [Parameter(Mandatory=$false)][switch]$All,
    [string]$UseCaseRoot = "core\usecases\core",
    [string]$ConnectionName = "local_pbip",
    [int]$MaxIterations = 5,
    [switch]$DryRun,
    [string]$ThemeName,
    [switch]$UseAuroraData
)

$ErrorActionPreference = "Stop"

# Path Resolution - repo root = directory containing both "core" and "tooling" (repo root, not products/fabric_powerbi)
$script:RepoRoot = $PSScriptRoot
while ($script:RepoRoot) {
    if ((Test-Path (Join-Path $script:RepoRoot "core")) -and (Test-Path (Join-Path $script:RepoRoot "tooling"))) { break }
    $script:RepoRoot = Split-Path -Parent $script:RepoRoot
}
if (-not $script:RepoRoot) { throw "Repo root (directory containing 'core' and 'tooling') not found from $PSScriptRoot" }
$script:ToolsRoot = Join-Path $script:RepoRoot "tooling"
$script:OrchestratorRoot = $PSScriptRoot
Push-Location $script:RepoRoot

# Aurora domain semantic models: central mapping (prefix <-> domain name <-> model path, data contract)
. "$PSScriptRoot\AuroraDomainMapping.ps1"
. "$PSScriptRoot\Phase5ReportGeneration.ps1"

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

# Returns the use case folder name (e.g. COM-001_Sales_Performance) for report PBIP naming; fallback: $UcId
function Get-UseCaseReportFolderBaseName {
    param([string]$UcId)
    $absRoot = Join-Path $script:RepoRoot $UseCaseRoot
    if (-not (Test-Path $absRoot)) { return $UcId }
    $dir = Get-ChildItem $absRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "$UcId*" } | Select-Object -First 1
    if ($dir) { return $dir.Name }
    return $UcId
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

# State Tracking (validateErrors for learning loop: phase, path, message, source, timestamp)
$state = @{
    scopeType = $scopeType
    scopeName = $scopeName
    iteration = 0
    phase = "init"
    errors = @()
    warnings = @()
    validateErrors = @()
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
# Use ALL use cases per domain (from repo) so _Measures.tmdl is cumulative; reports stay on same model without losing other UCs' measures.
$state.phase = "measure_generation"
$state.iteration = 2
$state.domainMeasurePaths = @()

$byDomain = Get-UseCaseIdsGroupedByDomain -UseCaseIds $script:SelectedUseCaseIds
$byDomainAll = Get-UseCaseIdsGroupedByDomain -UseCaseIds $allIdsFromRoot
$ucRootForScript = $UseCaseRoot -replace '\\', '/'
Invoke-WithRetry "Generate Measures (Aurora per domain)" {
    foreach ($domainName in $byDomain.Keys) {
        $ucIdsForMeasures = if ($byDomainAll[$domainName]) { @($byDomainAll[$domainName]) } else { $byDomain[$domainName] }
        $tablesPath = Get-FabricDomainTablesPath -DomainName $domainName
        if (-not $tablesPath) {
            Write-Host "  WARNING: No Fabric model path for domain $domainName, skipping" -ForegroundColor Yellow
            continue
        }
        $modelPath = Get-FabricDomainModelPath -DomainName $domainName
        $defPath = Join-Path $script:RepoRoot (Join-Path $modelPath "definition")
        if (-not (Test-Path $defPath)) {
            New-Item -ItemType Directory -Path (Join-Path $script:RepoRoot $tablesPath) -Force | Out-Null
            $modelContent = "model Model`r`n`tculture: de-DE`r`n`tdefaultPowerBIDataSourceVersion: PowerBI_V3`r`n`r`n"
            $utf8 = New-Object System.Text.UTF8Encoding $false
            [System.IO.File]::WriteAllText((Join-Path $script:RepoRoot (Join-Path $modelPath "definition\model.tmdl")), $modelContent, $utf8)
        }
        Write-Host "  Domain $domainName : $($ucIdsForMeasures -join ', ')" -ForegroundColor Gray
        & ./tooling/generation/generate_tmdl_measures.ps1 `
            -UseCase $ucIdsForMeasures `
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
            throw "Fabric measures file not created: $measuresPath"
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
    $outDir = Join-Path $script:OrchestratorRoot "out"
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    foreach ($domainName in $byDomain.Keys) {
        $goldContract = Get-AuroraDomainDataContract -DomainName $domainName
        $tablesPath = Get-FabricDomainTablesPath -DomainName $domainName
        $targetDir = Join-Path $script:RepoRoot $tablesPath
        if (-not $goldContract -or -not (Test-Path (Join-Path $script:RepoRoot $goldContract))) {
            Write-Host "  WARNING: Data contract not found for $domainName : $goldContract" -ForegroundColor Yellow
            continue
        }
        $requiredTables = Get-AuroraDomainRequiredTables -DomainName $domainName
        $domainDefPath = Join-Path $script:RepoRoot (Get-FabricDomainDefinitionPath -DomainName $domainName)
        if ($UseAuroraData) {
            & (Join-Path $script:OrchestratorRoot "table_ops.ps1") `
                -Operation "WriteExpressionsTmdl" `
                -DefinitionPath $domainDefPath `
                -ErrorAction Stop | Out-Null
        }
        $createdTables = 0
        $partitionStyle = if ($UseAuroraData) { "GoldDataPath" } else { "Blank" }
        foreach ($tableName in $requiredTables) {
            $tmdlPath = Join-Path $targetDir "$tableName.tmdl"
            if (Test-Path $tmdlPath) {
                Write-Host "  [$domainName] Table exists: $tableName" -ForegroundColor Gray
                continue
            }
            try {
                & (Join-Path $script:OrchestratorRoot "table_ops.ps1") `
                    -Operation "CreateFromContract" `
                    -DataContractPath (Join-Path $script:RepoRoot $goldContract) `
                    -TableName $tableName `
                    -DefinitionPath $domainDefPath `
                    -PartitionSourceStyle $partitionStyle `
                    -ErrorAction Stop | Out-Null
                $createdTables++
                Write-Host "  [$domainName] Created table: $tableName" -ForegroundColor Green
            } catch {
                Write-Host "  WARNING: [$domainName] Could not create table $tableName : $_" -ForegroundColor Yellow
            }
        }
        Write-Host "  [$domainName] Tables created: $createdTables/$($requiredTables.Count)" -ForegroundColor Green
        # Patch descriptions from contract into existing table TMDL (so existing tables get /// from contract)
        try {
            $domainDefPath = Join-Path $script:RepoRoot (Get-FabricDomainDefinitionPath -DomainName $domainName)
            & (Join-Path $script:OrchestratorRoot "table_ops.ps1") `
                -Operation "PatchDescriptionsFromContract" `
                -DataContractPath (Join-Path $script:RepoRoot $goldContract) `
                -DefinitionPath $domainDefPath `
                -ErrorAction Stop | Out-Null
        } catch {
            Write-Host "  (PatchDescriptionsFromContract optional: $_)" -ForegroundColor DarkGray
        }
        # Partition source: GoldDataPath (Aurora gold parquet) or Blank (local PBIP without Fabric)
        try {
            if ($UseAuroraData) {
                & (Join-Path $script:OrchestratorRoot "table_ops.ps1") `
                    -Operation "PatchPartitionSourceToGoldDataPath" `
                    -DefinitionPath $domainDefPath `
                    -ErrorAction Stop | Out-Null
            } else {
                & (Join-Path $script:OrchestratorRoot "table_ops.ps1") `
                    -Operation "PatchPartitionSourceToBlank" `
                    -DefinitionPath $domainDefPath `
                    -ErrorAction Stop | Out-Null
            }
        } catch {
            Write-Host "  (Partition source patch optional: $_)" -ForegroundColor DarkGray
        }
        # Integer/numeric columns: do not summarize (Best Practice)
        try {
            $domainDefPath = Join-Path $script:RepoRoot (Get-FabricDomainDefinitionPath -DomainName $domainName)
            & (Join-Path $script:OrchestratorRoot "table_ops.ps1") `
                -Operation "PatchAddSummarizeByNone" `
                -DefinitionPath $domainDefPath `
                -ErrorAction Stop | Out-Null
        } catch {
            Write-Host "  (PatchAddSummarizeByNone optional: $_)" -ForegroundColor DarkGray
        }
        $firstUc = $byDomain[$domainName][0]
        if ($firstUc) {
            try {
                & (Join-Path $script:OrchestratorRoot "table_ops.ps1") -Operation "ExportFromContract" -DataContractPath (Join-Path $script:RepoRoot $goldContract) -UseCase $firstUc -OutJsonPath (Join-Path $outDir "table_ops_$firstUc.json") -ErrorAction Stop | Out-Null
            } catch {
                Write-Host "  (ExportFromContract optional: $_)" -ForegroundColor DarkGray
            }
        }
    }
}

# 3.2b Sync model.tmdl: ensure "ref table X" for every table in definition/tables/ (so the semantic model includes all tables)
Invoke-WithRetry "Sync model.tmdl refs" {
    foreach ($domainName in $byDomain.Keys) {
        $defPath = Join-Path $script:RepoRoot (Get-FabricDomainDefinitionPath -DomainName $domainName)
        $modelPath = Join-Path $defPath "model.tmdl"
        $tablesDir = Join-Path $defPath "tables"
        if (-not (Test-Path $modelPath) -or -not (Test-Path $tablesDir)) { continue }
        $tableFiles = Get-ChildItem $tablesDir -Filter "*.tmdl" -File -ErrorAction SilentlyContinue
        $tableNames = $tableFiles | ForEach-Object { $_.BaseName } | Sort-Object -Unique
        if ($tableNames.Count -eq 0) { continue }
        $modelRaw = Get-Content -Raw -Path $modelPath
        $existingRefs = [regex]::Matches($modelRaw, '(?m)^ref\s+table\s+(\S+)\s*$') | ForEach-Object { $_.Groups[1].Value }
        $toAdd = $tableNames | Where-Object { $existingRefs -notcontains $_ }
        if ($toAdd.Count -gt 0) {
            $append = ($toAdd | ForEach-Object { "ref table $_" }) -join [Environment]::NewLine
            $utf8 = New-Object System.Text.UTF8Encoding $false
            $newContent = $modelRaw.TrimEnd() + [Environment]::NewLine + $append + [Environment]::NewLine
            [System.IO.File]::WriteAllText($modelPath, $newContent, $utf8)
            Write-Host "  [$domainName] model.tmdl: added ref table for $($toAdd -join ', ')" -ForegroundColor Green
        }
    }
}

# 3.3 Create Relationships from UseCase_Bracket.yaml (using $script:SelectedUseCaseIds; write to Fabric dist per domain)
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
    $outDir = Join-Path $script:OrchestratorRoot "out"
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    $created = 0
    foreach ($useCaseDir in $bracketDirs) {
        $bracketPath = "$($useCaseDir.FullName)\UseCase_Bracket.yaml"
        $ucId = ($useCaseDir.Name -split '_', 2)[0]
        $domainName = Get-DomainNameFromUseCaseId -UcId $ucId
        $defPath = if ($domainName) { Join-Path $script:RepoRoot (Get-FabricDomainDefinitionPath -DomainName $domainName) } else { $null }
        $relJsonPath = Join-Path $outDir "relationship_ops_$ucId.json"
        try {
            $relArgs = @(
                "-Operation", "CreateFromBracket",
                "-BracketPath", $bracketPath,
                "-OutJsonPath", $relJsonPath
            )
            if ($defPath) { $relArgs += "-DefinitionPath", $defPath }
            else { $relArgs += "-ConnectionName", "local_pbip" }
            & (Join-Path $script:OrchestratorRoot "relationship_ops.ps1") @relArgs -ErrorAction Stop | Out-Null
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
    $outDir = Join-Path $script:OrchestratorRoot "out"
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    $created = 0
    foreach ($useCaseDir in $bracketDirs) {
        $bracketPath = "$($useCaseDir.FullName)\UseCase_Bracket.yaml"
        $ucId = ($useCaseDir.Name -split '_', 2)[0]
        $hierJsonPath = Join-Path $outDir "hierarchy_ops_$ucId.json"
        try {
            & (Join-Path $script:OrchestratorRoot "hierarchy_ops.ps1") `
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

# 3.5 Write hierarchy blocks into dimension table TMDL (per domain, from gold contract)
Invoke-WithRetry "Write Hierarchies to TMDL" {
    foreach ($domainName in $byDomain.Keys) {
        $goldContract = Get-AuroraDomainDataContract -DomainName $domainName
        $domainDefPath = Join-Path $script:RepoRoot (Get-FabricDomainDefinitionPath -DomainName $domainName)
        if (-not $goldContract -or -not (Test-Path (Join-Path $script:RepoRoot $goldContract))) {
            Write-Host "  [$domainName] No gold contract; skip WriteToTmdl" -ForegroundColor DarkGray
            continue
        }
        try {
            & (Join-Path $script:OrchestratorRoot "hierarchy_ops.ps1") `
                -Operation "WriteToTmdl" `
                -DefinitionPath $domainDefPath `
                -DataContractPath (Join-Path $script:RepoRoot $goldContract) `
                -ErrorAction Stop | Out-Null
            Write-Host "  [$domainName] Hierarchies written to table TMDL" -ForegroundColor Green
        } catch {
            Write-Host "  WARNING: [$domainName] WriteToTmdl : $_" -ForegroundColor Yellow
        }
    }
}

# PHASE 4: VALIDATION
$state.phase = "validation"
$state.iteration = 4

Invoke-WithRetry "Validate TMDL Syntax" {
    $validatorScript = Join-Path $script:ToolsRoot "validation\validate_tmdl.ps1"
    if (-not (Test-Path $validatorScript)) {
        Write-Host "  validate_tmdl.ps1 not found, skipping" -ForegroundColor Yellow
        return
    }
    foreach ($measuresPath in $state.domainMeasurePaths) {
        if (-not (Test-Path $measuresPath)) { continue }
        $definitionDir = Split-Path (Split-Path $measuresPath -Parent) -Parent
        if (-not (Test-Path $definitionDir)) {
            Write-Host "  Definition folder not found: $definitionDir" -ForegroundColor Yellow
            continue
        }
        $domainLabel = Split-Path (Split-Path $definitionDir -Parent) -Leaf
        Write-Host "  Validating TMDL [$domainLabel]..." -ForegroundColor Gray
        & $validatorScript -TmdlPath $definitionDir -AutoFix
        if ($LASTEXITCODE -ne 0) {
            throw "TMDL validation failed for $definitionDir. Check bpa-rules-tmdl.json for rule violations."
        }
    }
    if ($state.domainMeasurePaths.Count -eq 0) {
        Write-Host "  No domain measure paths to validate, skipping" -ForegroundColor Yellow
        return
    }
    Write-Host "  OK TMDL validation passed (all domain models)" -ForegroundColor Green
}

# Semantic model: only definition.pbism if Desktop needs it; no .pbip for semantic model (reports have .pbip).
foreach ($domainName in $byDomain.Keys) {
    $modelPath = Join-Path $script:RepoRoot (Get-FabricDomainModelPath -DomainName $domainName)
    if (-not (Test-Path $modelPath)) { continue }
    $pbismPath = Join-Path $modelPath "definition.pbism"
    $pbismJson = @{
        '$schema' = "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json"
        version   = "4.2"
        settings  = @{}
    } | ConvertTo-Json -Depth 3
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($pbismPath, $pbismJson, $utf8NoBom)
    Write-Host "  definition.pbism written: $pbismPath" -ForegroundColor Gray
}

Invoke-WithRetry "Run Quality Checks" {
    $checksScript = Join-Path $script:ToolsRoot "run_all_checks.ps1"
    
    if (-not (Test-Path $checksScript)) {
        Write-Host "  run_all_checks.ps1 not found, skipping" -ForegroundColor Yellow
        return
    }
    $useCaseIdsArg = $script:SelectedUseCaseIds -join ","
    $bpaOutput = & $checksScript -UseCaseIds $useCaseIdsArg -RepoRoot $script:RepoRoot 2>&1 | Out-String
    $errorLines = $bpaOutput -split [Environment]::NewLine | Where-Object { $_ -match "ERROR|FAIL" }
    
    if ($errorLines.Count -gt 0) {
        Write-Host "  Found $($errorLines.Count) error/fail line(s)" -ForegroundColor Red
        $state.warnings += "Quality checks: $($errorLines.Count) errors"
        throw "Quality checks reported errors. Fix and run tooling\run_stage1_checks.ps1"
    }
    Write-Host "  Quality checks passed" -ForegroundColor Green
}

# PHASE 5: REPORT GENERATION (UX Engine: page_scaffold_generator, overview + detail, datasetReference)
$phase5Block = {
    Invoke-Phase5ReportGeneration
}
Invoke-WithRetry -PhaseName "Generate Report from Template" -Script $phase5Block

# PHASE 6: VALIDATE FABRIC OUTPUT (two-layer: run_fabric_checks -> structure -> pbi-tools compile)
$state.phase = "validate_fabric_output"
$state.iteration = 6
$distReportRoot = Join-Path $script:RepoRoot "products\fabric_powerbi\dist"
$distRootParam = "products/fabric_powerbi/dist"

Invoke-WithRetry "Validate Fabric output" {
    # (1) Best-practice rules: TMDL, PBIP readiness, DAX, measures vs KPI
    $fabricChecksScript = Join-Path $script:RepoRoot "products\fabric_powerbi\tooling\run_fabric_checks.ps1"
    if (-not (Test-Path $fabricChecksScript)) {
        throw "run_fabric_checks.ps1 not found at $fabricChecksScript"
    }
    $fabricOut = & $fabricChecksScript -DistRoot $distRootParam 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        $state.validateErrors += @{
            timestamp = (Get-Date -Format "o")
            phase = "Validate Fabric output"
            path = $distRootParam
            message = ($fabricOut -split [Environment]::NewLine | Select-Object -First 20) -join " "
            source = "run_fabric_checks"
        }
        throw "Fabric checks failed (exit $LASTEXITCODE). Fix TMDL/PBIP/DAX/measures and retry."
    }
    Write-Host "  run_fabric_checks passed" -ForegroundColor Green

    # (2) Structure: check_report_structure, validate_pbip per PBIP folder
    $checkReportScript = Join-Path $script:RepoRoot "products\fabric_powerbi\tooling\check_report_structure.ps1"
    if (Test-Path $checkReportScript) {
        & $checkReportScript -DistRoot $distRootParam -RepoRoot $script:RepoRoot | Out-Null
        if ($LASTEXITCODE -ne 0) {
            $state.validateErrors += @{ timestamp = (Get-Date -Format "o"); phase = "Validate Fabric output"; path = $distRootParam; message = "check_report_structure failed"; source = "check_report_structure" }
            throw "Report structure check failed. Fix definition/report.json and datasetReference."
        }
        Write-Host "  check_report_structure passed" -ForegroundColor Green
    }
    $validatePbipScript = Join-Path $script:ToolsRoot "validation\pbip\validate_pbip.ps1"
    if (Test-Path $validatePbipScript) {
        # validate_pbip expects report artifact; run only on Report folders, not on SemanticModel
        $pbipDirs = @()
        Get-ChildItem $distReportRoot -Directory -Filter "*.Report" -ErrorAction SilentlyContinue | ForEach-Object { $pbipDirs += $_.FullName }
        foreach ($dir in $pbipDirs) {
            $pbipFile = Get-ChildItem -Path $dir -Filter "*.pbip" -File -ErrorAction SilentlyContinue | Select-Object -First 1
            if (-not $pbipFile) { continue }
            & $validatePbipScript -Root $dir 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                $state.validateErrors += @{ timestamp = (Get-Date -Format "o"); phase = "Validate Fabric output"; path = $dir; message = "validate_pbip failed for $dir"; source = "validate_pbip" }
                throw "PBIP validation failed for $dir"
            }
        }
        Write-Host "  validate_pbip passed (PBIP folders with .pbip)" -ForegroundColor Green
    }

    # (3) pbi-tools compile (optional gate): proxy for "would Desktop open?"
    $pbiTools = Get-Command pbi-tools -ErrorAction SilentlyContinue
    if (-not $pbiTools) {
        Write-Host "  WARNING: pbi-tools not found. Skipping compile step. Install for loadable gate (e.g. winget install pbi-tools)." -ForegroundColor Yellow
        $state.warnings += "pbi-tools not installed; compile step skipped"
    } else {
        $compileDirs = @()
        foreach ($domainName in $byDomain.Keys) {
            $modelPath = Join-Path $script:RepoRoot (Get-FabricDomainModelPath -DomainName $domainName)
            if (Test-Path $modelPath) { $compileDirs += $modelPath }
        }
        Get-ChildItem $distReportRoot -Directory -Filter "*.Report" -ErrorAction SilentlyContinue | ForEach-Object { $compileDirs += $_.FullName }
        foreach ($pbipFolder in $compileDirs) {
            $compileOut = & pbi-tools compile $pbipFolder 2>&1 | Out-String
            if ($LASTEXITCODE -ne 0) {
                $state.validateErrors += @{
                    timestamp = (Get-Date -Format "o")
                    phase = "Validate Fabric output"
                    path = $pbipFolder
                    message = ($compileOut -split [Environment]::NewLine | Select-Object -First 30) -join " "
                    source = "pbi-tools compile"
                }
                throw "pbi-tools compile failed for $pbipFolder. $compileOut"
            }
            Write-Host "  compile OK: $([System.IO.Path]::GetFileName($pbipFolder))" -ForegroundColor Green
        }
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
if ($state.validateErrors.Count -gt 0) {
    Write-Host ([Environment]::NewLine + "Validate errors (for learning):") -ForegroundColor Yellow
    $state.validateErrors | ForEach-Object { Write-Host "  [$($_.source)] $($_.path): $($_.message)" -ForegroundColor Gray }
    $errLogPath = Join-Path $PSScriptRoot "out\build_errors.json"
    $errDir = Split-Path -Parent $errLogPath
    if (-not (Test-Path $errDir)) { New-Item -ItemType Directory -Path $errDir -Force | Out-Null }
    $state.validateErrors | ConvertTo-Json -Depth 4 | Set-Content -Path $errLogPath -Encoding utf8
    Write-Host "  Logged: $errLogPath" -ForegroundColor Gray
}

Write-Host ([Environment]::NewLine + "Output (Fabric dist):") -ForegroundColor Cyan
foreach ($domainName in $byDomain.Keys) {
    $outputModel = Get-FabricDomainModelPath -DomainName $domainName
    Write-Host "  [$domainName] $outputModel" -ForegroundColor Gray
}
Write-Host "  Reports: products\fabric_powerbi\dist\<UC>.Report (datasetReference = ..\<Domain>.SemanticModel)" -ForegroundColor Gray

Write-Host ([Environment]::NewLine + "Next Steps:") -ForegroundColor Yellow
Write-Host "  1. Open a domain model in Power BI Desktop (e.g. products\fabric_powerbi\dist\Commercial.SemanticModel)" -ForegroundColor Gray
Write-Host "  2. Open a report: products\fabric_powerbi\dist\<UC>.Report (references that UC's domain model in same dist)" -ForegroundColor Gray
Write-Host "  3. Use -Domain <name> or -UseCase <id> to build only that scope" -ForegroundColor Gray

# Export state
$stateFile = Join-Path $PSScriptRoot "last_run_state.json"
$stateJson = $state | ConvertTo-Json -Depth 5
$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($stateFile, $stateJson, $utf8)
Write-Host ([Environment]::NewLine + "State saved: $stateFile") -ForegroundColor Green

if ($state.errors.Count -gt 0) {
    exit 1
}
