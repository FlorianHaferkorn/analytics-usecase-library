Param(
  [string]$Root = "."
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath {
  param([string]$ProvidedPath,[string]$DefaultRelative)
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

$rootPath = Resolve-RepoPath -ProvidedPath $Root -DefaultRelative "."
if (-not $rootPath) { throw "Root path not found." }

Write-Host "Running Stage 1 checks (fail-fast)..." -ForegroundColor Cyan

$checks = @(
  @{ Path = "tooling/validation/check_schema_validation.ps1"; Args = @("-Root", $rootPath, "-FailOnError") },
  @{ Path = "tooling/validation/validate_factsheets.ps1"; Args = @("-UseCasesRoot", (Join-Path $rootPath "core\usecases"), "-FailOnError") },
  @{ Path = "tooling/validation/check_factsheet_vs_kpi.ps1"; Args = @("-UseCasesRoot", (Join-Path $rootPath "core\usecases"), "-KpiCatalogRoot", (Join-Path $rootPath "core\kpi_catalog"), "-FailOnMissing") },
  @{ Path = "tooling/validation/validate_kpi_catalog.ps1"; Args = @("-KpiCatalogRoot", (Join-Path $rootPath "core\kpi_catalog"), "-FailOnError") },
  @{ Path = "tooling/validation/check_action_codes_vs_kpi.ps1"; Args = @("-ActionCodesRoot", (Join-Path $rootPath "core\action_codes"), "-KpiCatalogRoot", (Join-Path $rootPath "core\kpi_catalog"), "-FailOnError") },
  @{ Path = "tooling/validation/check_factsheet_action_codes.ps1"; Args = @("-UseCasesRoot", (Join-Path $rootPath "core\usecases"), "-ActionCodesRoot", (Join-Path $rootPath "core\action_codes"), "-FailOnError") },
  @{ Path = "tooling/validation/check_decision_spines.ps1"; Args = @("-UseCasesRoot", (Join-Path $rootPath "core\usecases"), "-MapPath", (Join-Path $rootPath "core\action_codes\decision_spines\DecisionSpine_UseCase_Map.yaml"), "-DecisionSpinesRoot", (Join-Path $rootPath "core\action_codes\decision_spines"), "-FailOnError") },
  @{ Path = "tooling/validation/check_duplicate_ids.ps1"; Args = @("-Root", $rootPath, "-FailOnError") },
  @{ Path = "tooling/validation/check_ssot_markers.ps1"; Args = @("-Root", $rootPath, "-FailOnError") },
  @{ Path = "tooling/maintenance/check_docs_refs.ps1"; Args = @("-Root", $rootPath) },
  @{ Path = "tooling/validation/check_forbidden_content.ps1"; Args = @("-Root", $rootPath, "-FailOnError") },
  @{ Path = "tooling/validation/check_validate_data_contracts.ps1"; Args = @("-Root", $rootPath, "-FailOnError") },
  @{ Path = "tooling/validation/check_registry_builder.ps1"; Args = @("-Root", $rootPath, "-FailOnError") }
)

$resultsDir = Join-Path -Path $rootPath -ChildPath "tooling\validation\results"
if (-not (Test-Path $resultsDir)) { New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null }

$checkResults = @()
$overallStatus = "pass"

foreach ($check in $checks) {
  $full = Join-Path -Path $rootPath -ChildPath $check.Path
  if (-not (Test-Path $full)) { throw "Missing check: $($check.Path)" }
  Write-Host "START $($check.Path)"
  & $full @($check.Args)
  $exitCode = $LASTEXITCODE
  $status = if ($exitCode -eq 0) { "pass" } else { "fail" }
  $checkResults += @{ check = $check.Path; status = $status; exit_code = $exitCode }
  if ($exitCode -ne 0) {
    Write-Host "FAIL $($check.Path) ($exitCode)"
    $overallStatus = "fail"
    # Write partial results before failing
    $resultsPayload = @{
      timestamp = (Get-Date -Format "o")
      stage = "stage1"
      overall_status = $overallStatus
      checks = $checkResults
    }
    $resultsPayload | ConvertTo-Json -Depth 4 | Out-File -FilePath (Join-Path $resultsDir "latest_results.json") -Encoding utf8
    exit $exitCode
  }
  Write-Host "OK $($check.Path)"
}

# Write results on success
$resultsPayload = @{
  timestamp = (Get-Date -Format "o")
  stage = "stage1"
  overall_status = $overallStatus
  checks = $checkResults
}
$resultsPayload | ConvertTo-Json -Depth 4 | Out-File -FilePath (Join-Path $resultsDir "latest_results.json") -Encoding utf8

Write-Host "Stage 1 checks passed. Results written to tooling/validation/results/latest_results.json" -ForegroundColor Green
