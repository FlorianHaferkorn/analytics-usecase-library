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
  @{ Path = "_internal/tools/validation/check_schema_validation.ps1"; Args = @("-Root", $rootPath, "-FailOnError") },
  @{ Path = "_internal/tools/validation/validate_factsheets.ps1"; Args = @("-UseCasesRoot", (Join-Path $rootPath "usecases"), "-FailOnError") },
  @{ Path = "_internal/tools/validation/check_factsheet_vs_kpi.ps1"; Args = @("-UseCasesRoot", (Join-Path $rootPath "usecases"), "-KpiCatalogRoot", (Join-Path $rootPath "framework\kpi_catalog"), "-FailOnMissing") },
  @{ Path = "_internal/tools/validation/check_action_codes_vs_kpi.ps1"; Args = @("-ActionCodesRoot", (Join-Path $rootPath "framework\action_codes"), "-KpiCatalogRoot", (Join-Path $rootPath "framework\kpi_catalog"), "-FailOnError") },
  @{ Path = "_internal/tools/validation/check_factsheet_action_codes.ps1"; Args = @("-UseCasesRoot", (Join-Path $rootPath "usecases"), "-ActionCodesRoot", (Join-Path $rootPath "framework\action_codes"), "-FailOnError") },
  @{ Path = "_internal/tools/validation/check_usecase_actioncode_map.ps1"; Args = @("-UseCasesRoot", (Join-Path $rootPath "usecases"), "-MapPath", (Join-Path $rootPath "usecases\UseCase_ActionCode_Map.yaml"), "-ActionCodesRoot", (Join-Path $rootPath "framework\action_codes"), "-FailOnError") },
  @{ Path = "_internal/tools/validation/check_decision_spines.ps1"; Args = @("-UseCasesRoot", (Join-Path $rootPath "usecases"), "-MapPath", (Join-Path $rootPath "framework\action_codes\decision_spines\DecisionSpine_UseCase_Map.yaml"), "-DecisionSpinesRoot", (Join-Path $rootPath "framework\action_codes\decision_spines"), "-FailOnError") },
  @{ Path = "_internal/tools/validation/check_duplicate_ids.ps1"; Args = @("-Root", $rootPath, "-FailOnError") },
  @{ Path = "_internal/tools/validation/check_ssot_markers.ps1"; Args = @("-Root", $rootPath, "-FailOnError") },
  @{ Path = "_internal/tools/maintenance/check_docs_refs.ps1"; Args = @("-Root", $rootPath) },
  @{ Path = "_internal/tools/validation/check_forbidden_content.ps1"; Args = @("-Root", $rootPath, "-FailOnError") }
)

foreach ($check in $checks) {
  $full = Join-Path -Path $rootPath -ChildPath $check.Path
  if (-not (Test-Path $full)) { throw "Missing check: $($check.Path)" }
  Write-Host "START $($check.Path)"
  & $full @($check.Args)
  if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL $($check.Path) ($LASTEXITCODE)"
    exit $LASTEXITCODE
  }
  Write-Host "OK $($check.Path)"
}

Write-Host "Stage 1 checks passed." -ForegroundColor Green
