Param(
  [string]$UseCasesRoot   = "core/usecases",
  [string]$KpiCatalogRoot = "core/kpi_catalog",
  [string]$DistRoot       = "products/fabric/powerbi/dist",
  [string]$TranscriptPath   = "internal/reviews/run_all_checks_transcript.txt",
  [string]$ReportPath       = "internal/reviews/run_all_checks_report.md",
  [string]$UseCaseIds,
  [string]$RepoRoot
)

$ErrorActionPreference = "Stop"

# Canonical repo root: explicit param or current location; normalize to avoid "path format not supported"
$script:RepoRootRaw = if ($RepoRoot) { $RepoRoot } else { (Get-Location).Path }
try {
  $script:RepoRoot = [System.IO.Path]::GetFullPath($script:RepoRootRaw)
} catch {
  $script:RepoRoot = $script:RepoRootRaw
}

function Resolve-FullPathSafe {
  param(
    [string]$PathValue
  )
  if ([string]::IsNullOrWhiteSpace($PathValue)) {
    return $null
  }
  try {
    return [System.IO.Path]::GetFullPath($PathValue)
  } catch {
    return $PathValue
  }
}

function Resolve-RepoPath {
  param(
    [string]$ProvidedPath,
    [string]$DefaultRelative
  )
  $repo = $script:RepoRoot
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) {
      try { return (Resolve-FullPathSafe ((Resolve-Path -Path $ProvidedPath).Path)) } catch { }
    }
    $candidate = Join-Path -Path $repo -ChildPath ($ProvidedPath -replace '/', [System.IO.Path]::DirectorySeparatorChar)
    if (Test-Path $candidate) {
      try { return (Resolve-FullPathSafe ((Resolve-Path -Path $candidate).Path)) } catch { return (Resolve-FullPathSafe $candidate) }
    }
  }
  if ($DefaultRelative) {
    $fallback = Join-Path -Path $repo -ChildPath ($DefaultRelative -replace '/', [System.IO.Path]::DirectorySeparatorChar)
    if (Test-Path $fallback) {
      try { return (Resolve-FullPathSafe ((Resolve-Path -Path $fallback).Path)) } catch { return (Resolve-FullPathSafe $fallback) }
    }
    return (Resolve-FullPathSafe $fallback)
  }
  return $null
}

$repoRoot = $script:RepoRoot

# Resolve paths; never pass null to child scripts (use repo-relative defaults so params always bind)
$useCasesRoot   = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative 'core/usecases'
$kpiCatalogRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative 'core/kpi_catalog'
$distRoot       = Resolve-RepoPath -ProvidedPath $DistRoot -DefaultRelative 'products/fabric/powerbi/dist'
if (-not $useCasesRoot)   { $useCasesRoot   = [System.IO.Path]::GetFullPath((Join-Path -Path $repoRoot -ChildPath 'core\usecases')) }
if (-not $kpiCatalogRoot) { $kpiCatalogRoot = [System.IO.Path]::GetFullPath((Join-Path -Path $repoRoot -ChildPath 'core\kpi_catalog')) }
if (-not $distRoot)       { $distRoot       = [System.IO.Path]::GetFullPath((Join-Path -Path $repoRoot -ChildPath 'products\fabric\powerbi\dist')) }
$factsheetsRoot = $useCasesRoot
$coreRoot = Join-Path -Path $useCasesRoot -ChildPath 'core'
if (Test-Path $coreRoot) {
  $factsheetsRoot = [System.IO.Path]::GetFullPath((Resolve-Path -Path $coreRoot).Path)
}

$reportDir = Split-Path -Parent ([System.IO.Path]::GetFullPath((Join-Path -Path $repoRoot -ChildPath ($ReportPath -replace '/', [System.IO.Path]::DirectorySeparatorChar))))
if ($reportDir -and -not (Test-Path $reportDir)) {
  New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

if ($UseCaseIds) {
  $script:ScopeUseCaseIds = @($UseCaseIds -split '[,;]' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
} else {
  $script:ScopeUseCaseIds = $null
}
$coreUseCasesDefault = @("COM-001", "COM-002", "COM-003", "COM-004", "FIN-001", "FIN-002", "OPS-001", "OPS-002", "OPS-003")
$useCasesToCheck = if ($script:ScopeUseCaseIds -and $script:ScopeUseCaseIds.Count -gt 0) { $script:ScopeUseCaseIds } else { $coreUseCasesDefault }

# Normalize transcript path to avoid "path format not supported" (e.g. on Start-Transcript)
$transcriptPath = if ([System.IO.Path]::IsPathRooted($TranscriptPath)) {
  $TranscriptPath
} else {
  Join-Path -Path $repoRoot -ChildPath ($TranscriptPath -replace '/', [System.IO.Path]::DirectorySeparatorChar)
}
$transcriptPath = Resolve-FullPathSafe $transcriptPath
$transcriptDir = [System.IO.Path]::GetDirectoryName($transcriptPath)
if ($transcriptDir -and -not (Test-Path $transcriptDir)) {
  New-Item -ItemType Directory -Path $transcriptDir -Force | Out-Null
}

$script:TranscriptActive = $false
try {
  $null = Start-Transcript -Path $transcriptPath -Force -ErrorAction SilentlyContinue
  if ($?) { $script:TranscriptActive = $true }
  if (-not $script:TranscriptActive) {
    Write-Host "WARNING: Transcript not started (path: $transcriptPath) - continuing without transcript." -ForegroundColor Yellow
  }
} catch {
  Write-Host "WARNING: Could not start transcript - continuing without transcript. $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "Running analytics-usecase-library checks..." -ForegroundColor Cyan
Write-Host "UseCases:   $useCasesRoot" -ForegroundColor DarkGray
Write-Host "Factsheets: $factsheetsRoot" -ForegroundColor DarkGray
Write-Host "KPI Catalog: $kpiCatalogRoot" -ForegroundColor DarkGray
Write-Host ""

$script:checkResults = @()

function Invoke-LocalScript {
  param(
    [string]$RelativePath,
    [object]$Arguments
  )
  $relativeNormalized = $RelativePath -replace '/', [System.IO.Path]::DirectorySeparatorChar
  $full = [System.IO.Path]::GetFullPath((Join-Path -Path $repoRoot -ChildPath $relativeNormalized))
  if (-not (Test-Path $full)) {
    Write-Host "Skip: $RelativePath (not found)" -ForegroundColor Yellow
    return
  }
  if ($Arguments -is [hashtable]) {
    $argText = ($Arguments.GetEnumerator() | ForEach-Object { "-$($_.Key) $($_.Value)" }) -join ' '
  } elseif ($Arguments -is [string[]]) {
    $argText = ($Arguments -join ' ')
  } else {
    $argText = ""
  }
  Write-Host ">> $RelativePath $argText" -ForegroundColor Cyan
  $startedAt = Get-Date
  $status = "ok"
  $errorMessage = ""
  $scriptExitCode = 0
  try {
    $global:LASTEXITCODE = 0
    if ($Arguments -is [hashtable]) {
      & $full @Arguments
    } elseif ($Arguments -is [string[]]) {
      & $full @Arguments
    } else {
      & $full
    }
    $scriptExitCode = $LASTEXITCODE
  } catch {
    $status = "failed"
    $errorMessage = $_.Exception.Message
    Write-Host ("  Error while running {0}:{1}  {2}" -f $RelativePath, [Environment]::NewLine, $_.Exception.Message) -ForegroundColor Red
    $scriptExitCode = if ($LASTEXITCODE -ne $null) { $LASTEXITCODE } else { 1 }
  }
  if ($status -eq "ok" -and $scriptExitCode -ne 0) {
    $status = "failed"
    if (-not $errorMessage) {
      $errorMessage = "Non-zero exit code: $scriptExitCode"
    }
  }
  $endedAt = Get-Date
  Write-Host ""

  $script:checkResults += [PSCustomObject]@{
    check = $RelativePath
    arguments = $argText
    status = $status
    started_at = $startedAt.ToString("s")
    duration_sec = [Math]::Round(($endedAt - $startedAt).TotalSeconds, 2)
    error = $errorMessage
  }
}

# 1) Validate FactSheets
Invoke-LocalScript -RelativePath "tooling/validation/validate_factsheets.ps1" -Arguments @{ UseCasesRoot = $factsheetsRoot }

# 2) Validate KPI catalogs
Invoke-LocalScript -RelativePath "tooling/validation/validate_kpi_catalog.ps1" -Arguments @{ KpiCatalogRoot = $kpiCatalogRoot }

# 3) Check coverage FactSheet vs KPI catalog
Invoke-LocalScript -RelativePath "tooling/validation/check_factsheet_vs_kpi.ps1" -Arguments @{ UseCasesRoot = $factsheetsRoot; KpiCatalogRoot = $kpiCatalogRoot }

# 4) Check measures vs KPI catalog (Fabric) – skip when dist folder does not exist
if (Test-Path $distRoot) {
  Invoke-LocalScript -RelativePath "products/fabric/powerbi/tooling/validation/check_measures_vs_kpi.ps1" -Arguments @{ DistRoot = $distRoot; KpiCatalogRoot = $kpiCatalogRoot }
}

# 5) Sanity-check docs and tooling references
# check_docs_refs.ps1 archived — tooling/generator/ consolidation in v1.0 Week 1

# 6) Docs -> KPI catalog references
Invoke-LocalScript -RelativePath "tooling/validation/check_docs_kpi_refs.ps1" -Arguments @{
  DocsRoot = (Join-Path $repoRoot "core\strategy_operating_model")
  KpiCatalogRoot = $kpiCatalogRoot
}

# 7) UseCase inventory vs Factsheets
Invoke-LocalScript -RelativePath "tooling/validation/check_usecase_inventory_vs_factsheets.ps1" -Arguments @{
  UseCasesRoot = $factsheetsRoot
  InventoryPath = (Join-Path $repoRoot "core\usecases\UseCase_Inventory.md")
}

# 8) KPI catalog unused in Factsheets (warning by default)
Invoke-LocalScript -RelativePath "tooling/validation/check_kpi_catalog_unused_in_factsheets.ps1" -Arguments @{
  UseCasesRoot = $factsheetsRoot
  KpiCatalogRoot = $kpiCatalogRoot
}

# 8a) Check for duplicate IDs (Action Codes, Use Cases, KPIs)
Invoke-LocalScript -RelativePath "tooling/validation/check_duplicate_ids.ps1" -Arguments @{ Root = $repoRoot }

# 8b) Check for forbidden content (KPI definitions in factsheets)
Invoke-LocalScript -RelativePath "tooling/validation/check_forbidden_content.ps1" -Arguments @{ Root = $repoRoot }

# 8c) Check for SSOT markers outside allowlist
Invoke-LocalScript -RelativePath "tooling/validation/check_ssot_markers.ps1" -Arguments @{ Root = $repoRoot }

# 9) Docs -> UseCase references
Invoke-LocalScript -RelativePath "tooling/validation/check_docs_usecase_refs.ps1" -Arguments @{
  DocsRoot = (Join-Path $repoRoot "core\strategy_operating_model")
  UseCasesRoot = $useCasesRoot
  InventoryPath = (Join-Path $repoRoot "core\usecases\UseCase_Inventory.md")
}

# 10) Action Codes -> KPI catalog references
Invoke-LocalScript -RelativePath "tooling/validation/check_action_codes_vs_kpi.ps1" -Arguments @{
  ActionCodesRoot = (Join-Path $repoRoot "core\action_codes")
  KpiCatalogRoot = $kpiCatalogRoot
}

# 11) OSS Stack gate
if (Test-Path (Join-Path $repoRoot "products\open_source_stack")) {
  Invoke-LocalScript -RelativePath "products/open_source_stack/tooling/run_oss_checks.ps1" -Arguments @{
    Root = $repoRoot
  }
}

# 11) Factsheets -> Action Codes existence
Invoke-LocalScript -RelativePath "tooling/validation/check_factsheet_action_codes.ps1" -Arguments @{
  UseCasesRoot = $factsheetsRoot
  ActionCodesRoot = (Join-Path $repoRoot "core\action_codes")
}

# 12) [REMOVED] UseCase ActionCode map consistency — map deleted in Lean 2.0 cutover

# 13) Decision Spines map consistency
Invoke-LocalScript -RelativePath "tooling/validation/check_decision_spines.ps1" -Arguments @{
  UseCasesRoot = $useCasesRoot
  MapPath = (Join-Path $repoRoot "core\action_codes\decision_spines\DecisionSpine_UseCase_Map.yaml")
  DecisionSpinesRoot = (Join-Path $repoRoot "core\action_codes\decision_spines")
}

# 14) [REMOVED] Factsheet action_codes vs UseCase map — map deleted in Lean 2.0 cutover

# 15) Factsheet layout vs templates (business only; technical template removed in Lean 2.0)
Invoke-LocalScript -RelativePath "tooling/validation/check_factsheet_layout.ps1" -Arguments @{
  UseCasesRoot = $factsheetsRoot
  BusinessTemplate = (Join-Path $repoRoot "core\usecases\templates\usecase_factsheet_business.md")
}

# 16) KPI catalog vs Measure Dictionaries
Invoke-LocalScript -RelativePath "tooling/validation/check_kpi_vs_measure_dictionary.ps1" -Arguments @{
  KpiCatalogRoot = $kpiCatalogRoot
  MeasureDictRoot = (Join-Path $repoRoot "core\semantic_models\domains")
}

# 17) DAX definitions vs Measure Dictionaries
Invoke-LocalScript -RelativePath "tooling/validation/check_dax_vs_measure_dictionary.ps1" -Arguments @{ UseCasesRoot = $factsheetsRoot }

# 18) Measure Dictionaries vs Gold contracts
Invoke-LocalScript -RelativePath "tooling/validation/check_measure_dictionary_vs_gold.ps1" -Arguments @{
  MeasureDictRoot = (Join-Path $repoRoot "core\semantic_models\domains")
  GoldRoot = (Join-Path $repoRoot "core\data_contracts\domains")
}

# 19) TMDL vs Measure Dictionaries (Fabric) – skip when dist does not exist
if (Test-Path $distRoot) {
  Invoke-LocalScript -RelativePath "products/fabric/powerbi/tooling/validation/check_tmdl_vs_measure_dictionary.ps1" -Arguments @{
    MeasureDictRoot = (Join-Path $repoRoot "core\semantic_models\domains")
    DistRoot = $distRoot
  }
}

# 19a) DAX best practices in TMDL measures (Fabric)
if (Test-Path $distRoot) {
  Invoke-LocalScript -RelativePath "products/fabric/powerbi/tooling/validation/check_dax_best_practices.ps1" -Arguments @{ DistRoot = $distRoot }
}

# 19b) Pre-generation DAX check (params by name so no prompt)
foreach ($useCaseId in $useCasesToCheck) {
  Invoke-LocalScript -RelativePath "tooling/validation/check_dax_before_generation.ps1" -Arguments @{
    UseCaseId = $useCaseId
    UseCasesRoot = $useCasesRoot
    KpiCatalogRoot = $kpiCatalogRoot
  }
}

# 19c) DAX validation (validate DAX expressions) – only when dist has SemanticModel folders; never prompt
if ($distRoot -and (Test-Path $distRoot)) {
	$tmdlDirs = Get-ChildItem -Path $distRoot -Filter "*.SemanticModel" -Directory -ErrorAction SilentlyContinue
	foreach ($dir in $tmdlDirs) {
		$defPath = Join-Path $dir.FullName "definition"
		if (-not [string]::IsNullOrWhiteSpace($defPath) -and (Test-Path $defPath)) {
			Invoke-LocalScript -RelativePath "tooling/validation/validate_dax.ps1" -Arguments @{ TmdlPath = $defPath }
		}
	}
}

# 19d) Semantic model structure validation – same guard
if ($distRoot -and (Test-Path $distRoot)) {
	$tmdlDirs = Get-ChildItem -Path $distRoot -Filter "*.SemanticModel" -Directory -ErrorAction SilentlyContinue
	foreach ($dir in $tmdlDirs) {
		$defPath = Join-Path $dir.FullName "definition"
		if (-not [string]::IsNullOrWhiteSpace($defPath) -and (Test-Path $defPath)) {
			Invoke-LocalScript -RelativePath "tooling/validation/validate_semanticmodel.ps1" -Arguments @{ TmdlPath = $defPath }
		}
	}
}

# 19d2) TMDL BPA validation – same guard
if ($distRoot -and (Test-Path $distRoot)) {
	$tmdlDirs = Get-ChildItem -Path $distRoot -Filter "*.SemanticModel" -Directory -ErrorAction SilentlyContinue
	foreach ($dir in $tmdlDirs) {
		$defPath = Join-Path $dir.FullName "definition"
		if (-not [string]::IsNullOrWhiteSpace($defPath) -and (Test-Path $defPath)) {
			Invoke-LocalScript -RelativePath "tooling/validation/validate_tmdl.ps1" -Arguments @{ TmdlPath = $defPath }
		}
	}
}

# 19e) Use case → TMDL end-to-end validation – skip when dist missing so TmdlPath is never empty
if (-not [string]::IsNullOrWhiteSpace($distRoot)) {
  foreach ($useCaseId in $useCasesToCheck) {
    Invoke-LocalScript -RelativePath "tooling/validation/check_usecase_to_tmdl.ps1" -Arguments @{
      UseCaseId = $useCaseId
      UseCasesRoot = $useCasesRoot
      KpiCatalogRoot = $kpiCatalogRoot
      TmdlPath = $distRoot
    }
  }
}

# 19f) Report validation (Power BI report structure)
if ($distRoot -and (Test-Path $distRoot)) {
  $reportDirs = Get-ChildItem -Path $distRoot -Filter "*.Report" -Directory -Recurse -ErrorAction SilentlyContinue
  foreach ($reportDir in $reportDirs) {
    $currentValidatedReportPath = $reportDir.FullName
    if ([string]::IsNullOrWhiteSpace($currentValidatedReportPath)) {
      continue
    }
	Invoke-LocalScript -RelativePath "tooling/validation/validate_report.ps1" -Arguments @{ ReportPath = $currentValidatedReportPath }
	}
}

# 19g) Action code → report validation
foreach ($useCaseId in $useCasesToCheck) {
  $currentUseCaseReportPath = Join-Path $distRoot "$useCaseId.Report"
  if (Test-Path $currentUseCaseReportPath) {
		Invoke-LocalScript -RelativePath "products/fabric/powerbi/tooling/validation/check_actioncode_to_report.ps1" -Arguments @{
      UseCaseId = $useCaseId
  UseCasesRoot = $useCasesRoot
      ReportPath = $currentUseCaseReportPath
    }
	}
}

# 20) Mojibake scan
Invoke-LocalScript -RelativePath "tooling/validation/check_mojibake.ps1" -Arguments @{ Root = $repoRoot }

# 21) Markdownlint (MD010/MD041/MD047 — enforced, fails on error)
Invoke-LocalScript -RelativePath "tooling/validation/check_markdownlint.ps1" -Arguments @{ Root = $repoRoot; FailOnError = $true }

# 22) YAML format check (if parser available)
Invoke-LocalScript -RelativePath "tooling/validation/check_yaml_format.ps1" -Arguments @{ Root = $repoRoot }

# 23) Schema validation (Action Codes, Maps) via JSON Schema
Invoke-LocalScript -RelativePath "tooling/validation/check_schema_validation.ps1" -Arguments @{ Root = $repoRoot }

if ($script:TranscriptActive) { Stop-Transcript | Out-Null }

$totalChecks = $script:checkResults.Count
$failedChecks = ($script:checkResults | Where-Object { $_.status -ne "ok" }).Count
$consolidatedPath = if ([System.IO.Path]::IsPathRooted($ReportPath)) {
  $ReportPath
} else {
  Join-Path -Path $repoRoot -ChildPath ($ReportPath -replace '/', [System.IO.Path]::DirectorySeparatorChar)
}
$consolidatedPath = Resolve-FullPathSafe $consolidatedPath
$consolidatedDir = Split-Path -Parent $consolidatedPath
if ($consolidatedDir -and -not (Test-Path $consolidatedDir)) {
  New-Item -ItemType Directory -Path $consolidatedDir -Force | Out-Null
}

$transcriptLines = @()
if (Test-Path $transcriptPath) {
  $transcriptLines = Get-Content -Path $transcriptPath
}
$sections = @{}
$currentKey = $null
$currentLines = New-Object 'System.Collections.Generic.List[string]'
foreach ($line in $transcriptLines) {
  if ($line -match '^\>\>\s*(.+)$') {
    if ($currentKey) { $sections[$currentKey] = $currentLines.ToArray() }
    $currentKey = $matches[1].Trim()
    $currentLines = New-Object 'System.Collections.Generic.List[string]'
    continue
  }
  if ($currentKey) { $currentLines.Add($line) | Out-Null }
}
if ($currentKey) { $sections[$currentKey] = $currentLines.ToArray() }

$consolidated = @()
$consolidated += "# Run All Checks Report"
$consolidated += ""
$consolidated += "- Timestamp: $(Get-Date -Format 's')"
$consolidated += "- Repo: $repoRoot"
$consolidated += "- UseCasesRoot: $useCasesRoot"
$consolidated += "- FactsheetsRoot: $factsheetsRoot"
$consolidated += "- KpiCatalogRoot: $kpiCatalogRoot"
$consolidated += "- DistRoot: $distRoot"
$consolidated += "- Transcript: $transcriptPath"
$consolidated += ""
$consolidated += "## Summary"
$consolidated += ""
$consolidated += "- Total checks: $totalChecks"
$consolidated += "- Failed checks: $failedChecks"
$consolidated += ""
$consolidated += "## Checks"
$consolidated += ""
$consolidated += "| Check | Status | Duration (s) | Arguments | Error |"
$consolidated += "| --- | --- | ---: | --- | --- |"
foreach ($result in $script:checkResults) {
  $errorCell = $result.error
  if (-not $errorCell) { $errorCell = "" }
  $consolidated += "| $($result.check) | $($result.status) | $($result.duration_sec) | $($result.arguments) | $errorCell |"
}

$consolidated += ""
$consolidated += "## Detailed Output"
foreach ($result in $script:checkResults) {
  $key = ($result.check + ' ' + $result.arguments).Trim()
  $consolidated += ""
  $consolidated += "### $($result.check)"
  if ($sections.ContainsKey($key)) {
    $consolidated += ""
    $consolidated += '```text'
    $consolidated += $sections[$key]
    $consolidated += '```'
  } else {
    $consolidated += ""
    $consolidated += "_No transcript output captured for this check._"
  }
}

Set-Content -Path $consolidatedPath -Value $consolidated -Encoding UTF8

# Self-correction: persist failures for automation / KNOWN_ERRORS_AND_FIXES
$failuresDir = Join-Path -Path $repoRoot -ChildPath "internal\reviews"
if (-not (Test-Path $failuresDir)) { New-Item -ItemType Directory -Path $failuresDir -Force | Out-Null }
$failuresPath = Join-Path -Path $failuresDir -ChildPath "run_all_checks_failures.json"
if ($failedChecks -gt 0) {
  $failedList = $script:checkResults | Where-Object { $_.status -ne "ok" } | ForEach-Object {
    @{ check = $_.check; arguments = $_.arguments; error = $_.error; duration_sec = $_.duration_sec }
  }
  $failuresJson = @{
    timestamp = (Get-Date -Format "o")
    repoRoot = $repoRoot
    totalChecks = $totalChecks
    failedCount = $failedChecks
    failed = $failedList
  } | ConvertTo-Json -Depth 4
  Set-Content -Path $failuresPath -Value $failuresJson -Encoding UTF8
  Write-Host "Failures written to $failuresPath for self-correction / KNOWN_ERRORS_AND_FIXES" -ForegroundColor Yellow
  exit 1
} else {
  if (Test-Path $failuresPath) { Remove-Item -Path $failuresPath -Force -ErrorAction SilentlyContinue }
  Write-Host "All checks invoked. Review messages above for warnings or errors." -ForegroundColor Green
  Write-Host "Report written to: $consolidatedPath" -ForegroundColor DarkGray
}
