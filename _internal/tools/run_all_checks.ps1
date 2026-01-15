Param(
  [string]$UseCasesRoot   = "usecases",
  [string]$KpiCatalogRoot = "framework/kpi_catalog",
  [string]$DistRoot       = "dist",
  [string]$StatusReportPath = "_internal/reviews/run_all_checks_status.md",
  [string]$TranscriptPath   = "_internal/reviews/run_all_checks_transcript.txt"
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath {
  param(
    [string]$ProvidedPath,
    [string]$DefaultRelative
  )
  $repo = (Get-Location).Path
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    $candidate = Join-Path -Path $repo -ChildPath $ProvidedPath
    if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
  }
  if ($DefaultRelative) {
    $fallback = Join-Path -Path $repo -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  return $null
}

$repoRoot = (Get-Location).Path

$useCasesRoot   = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative 'usecases'
$kpiCatalogRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative 'framework/kpi_catalog'
$distRoot       = Resolve-RepoPath -ProvidedPath $DistRoot -DefaultRelative 'dist'

$reportPath = Resolve-RepoPath -ProvidedPath $StatusReportPath -DefaultRelative $StatusReportPath
if (-not $reportPath) {
  $reportPath = Join-Path -Path $repoRoot -ChildPath $StatusReportPath
}
$reportDir = Split-Path -Parent $reportPath
if ($reportDir -and -not (Test-Path $reportDir)) {
  New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

$transcriptPath = Resolve-RepoPath -ProvidedPath $TranscriptPath -DefaultRelative $TranscriptPath
if (-not $transcriptPath) {
  $transcriptPath = Join-Path -Path $repoRoot -ChildPath $TranscriptPath
}
$transcriptDir = Split-Path -Parent $transcriptPath
if ($transcriptDir -and -not (Test-Path $transcriptDir)) {
  New-Item -ItemType Directory -Path $transcriptDir -Force | Out-Null
}

Start-Transcript -Path $transcriptPath -Force | Out-Null

Write-Host "Running analytics-usecase-library checks..." -ForegroundColor Cyan
Write-Host "UseCases:   $useCasesRoot" -ForegroundColor DarkGray
Write-Host "KPI Catalog: $kpiCatalogRoot" -ForegroundColor DarkGray
Write-Host ""

$checkResults = @()

function Invoke-LocalScript {
  param(
    [string]$RelativePath,
    [object]$Arguments
  )
  $full = Join-Path -Path $repoRoot -ChildPath $RelativePath
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
  try {
    if ($Arguments -is [hashtable]) {
      & $full @Arguments
    } elseif ($Arguments -is [string[]]) {
      & $full @Arguments
    } else {
      & $full
    }
  } catch {
    $status = "failed"
    $errorMessage = $_.Exception.Message
    Write-Host ("  Error while running {0}:{1}  {2}" -f $RelativePath, [Environment]::NewLine, $_.Exception.Message) -ForegroundColor Red
  }
  if ($status -eq "ok" -and $LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
    $status = "failed"
    if (-not $errorMessage) {
      $errorMessage = "Non-zero exit code: $LASTEXITCODE"
    }
  }
  $endedAt = Get-Date
  Write-Host ""

  $checkResults += [PSCustomObject]@{
    check = $RelativePath
    arguments = $argText
    status = $status
    started_at = $startedAt.ToString("s")
    duration_sec = [Math]::Round(($endedAt - $startedAt).TotalSeconds, 2)
    error = $errorMessage
  }
}

# 1) Validate FactSheets
Invoke-LocalScript -RelativePath "_internal/tools/validation/validate_factsheets.ps1" -Arguments @("-UseCasesRoot", $useCasesRoot)

# 2) Validate KPI catalogs
Invoke-LocalScript -RelativePath "_internal/tools/validation/validate_kpi_catalog.ps1" -Arguments @("-KpiCatalogRoot", $kpiCatalogRoot)

# 3) Check coverage FactSheet vs KPI catalog
Invoke-LocalScript -RelativePath "_internal/tools/validation/check_factsheet_vs_kpi.ps1" -Arguments @("-UseCasesRoot", $useCasesRoot, "-KpiCatalogRoot", $kpiCatalogRoot)

# 4) Check measures vs KPI catalog
Invoke-LocalScript -RelativePath "_internal/tools/validation/check_measures_vs_kpi.ps1" -Arguments @("-DistRoot", $distRoot, "-KpiCatalogRoot", $kpiCatalogRoot)

# 5) Sanity-check docs and tooling references
Invoke-LocalScript -RelativePath "_internal/tools/maintenance/check_docs_refs.ps1" -Arguments @()

# 6) Docs -> KPI catalog references
Invoke-LocalScript -RelativePath "_internal/tools/validation/check_docs_kpi_refs.ps1" -Arguments @(
  "-DocsRoot", (Join-Path $repoRoot "docs"),
  "-KpiCatalogRoot", $kpiCatalogRoot
)

# 7) UseCase inventory vs Factsheets
Invoke-LocalScript -RelativePath "_internal/tools/validation/check_usecase_inventory_vs_factsheets.ps1" -Arguments @(
  "-UseCasesRoot", $useCasesRoot,
  "-InventoryPath", (Join-Path $repoRoot "usecases\UseCase_Inventory.md")
)

# 8) KPI catalog unused in Factsheets (warning by default)
Invoke-LocalScript -RelativePath "_internal/tools/validation/check_kpi_catalog_unused_in_factsheets.ps1" -Arguments @(
  "-UseCasesRoot", $useCasesRoot,
  "-KpiCatalogRoot", $kpiCatalogRoot
)

# 9) Docs -> UseCase references
Invoke-LocalScript -RelativePath "_internal/tools/validation/check_docs_usecase_refs.ps1" -Arguments @(
  "-DocsRoot", (Join-Path $repoRoot "docs"),
  "-UseCasesRoot", $useCasesRoot,
  "-InventoryPath", (Join-Path $repoRoot "usecases\UseCase_Inventory.md")
)

# 10) Action Codes -> KPI catalog references
Invoke-LocalScript -RelativePath "_internal/tools/validation/check_action_codes_vs_kpi.ps1" -Arguments @(
  "-ActionCodesRoot", (Join-Path $repoRoot "framework\action_codes"),
  "-KpiCatalogRoot", $kpiCatalogRoot
)

# 11) Factsheets -> Action Codes existence
Invoke-LocalScript -RelativePath "_internal/tools/validation/check_factsheet_action_codes.ps1" -Arguments @(
  "-UseCasesRoot", $useCasesRoot,
  "-ActionCodesRoot", (Join-Path $repoRoot "framework\action_codes")
)

# 12) KPI catalog vs Measure Dictionaries
Invoke-LocalScript -RelativePath "_internal/tools/validation/check_kpi_vs_measure_dictionary.ps1" -Arguments @{
  KpiCatalogRoot = $kpiCatalogRoot
  MeasureDictRoot = (Join-Path $repoRoot "semantic_models\domains")
}

# 13) DAX definitions vs Measure Dictionaries
Invoke-LocalScript -RelativePath "_internal/tools/validation/check_dax_vs_measure_dictionary.ps1" -Arguments @(
  "-UseCasesRoot", $useCasesRoot
)

# 14) Measure Dictionaries vs Gold contracts
Invoke-LocalScript -RelativePath "_internal/tools/validation/check_measure_dictionary_vs_gold.ps1" -Arguments @{
  MeasureDictRoot = (Join-Path $repoRoot "semantic_models\domains")
  GoldRoot = (Join-Path $repoRoot "data_contracts\domains")
}

# 15) TMDL vs Measure Dictionaries (optional if TMDL exists)
Invoke-LocalScript -RelativePath "_internal/tools/validation/check_tmdl_vs_measure_dictionary.ps1" -Arguments @{
  MeasureDictRoot = (Join-Path $repoRoot "semantic_models\domains")
  DistRoot = $distRoot
}

Stop-Transcript | Out-Null

$totalChecks = $checkResults.Count
$failedChecks = ($checkResults | Where-Object { $_.status -ne "ok" }).Count
$reportLines = @()
$reportLines += "# Run All Checks Status"
$reportLines += ""
$reportLines += "- Timestamp: $(Get-Date -Format 's')"
$reportLines += "- Repo: $repoRoot"
$reportLines += "- UseCasesRoot: $useCasesRoot"
$reportLines += "- KpiCatalogRoot: $kpiCatalogRoot"
$reportLines += "- DistRoot: $distRoot"
$reportLines += "- Transcript: $transcriptPath"
$reportLines += ""
$reportLines += "## Summary"
$reportLines += ""
$reportLines += "- Total checks: $totalChecks"
$reportLines += "- Failed checks: $failedChecks"
$reportLines += ""
$reportLines += "## Checks"
$reportLines += ""
$reportLines += "| Check | Status | Duration (s) | Arguments | Error |"
$reportLines += "| --- | --- | ---: | --- | --- |"
foreach ($result in $checkResults) {
  $errorCell = $result.error
  if (-not $errorCell) { $errorCell = "" }
  $reportLines += "| $($result.check) | $($result.status) | $($result.duration_sec) | $($result.arguments) | $errorCell |"
}

Set-Content -Path $reportPath -Value $reportLines -Encoding UTF8

Write-Host "All checks invoked. Review messages above for warnings or errors." -ForegroundColor Green
Write-Host "Status report written to: $reportPath" -ForegroundColor DarkGray
