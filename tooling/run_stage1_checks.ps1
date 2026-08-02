Param(
  [string]$Root = "."
)

$ErrorActionPreference = "Stop"

# Ensure powershell-yaml is loaded for check_validate_data_contracts.ps1 (CI and local).
# Soft-fail: environments without PSGallery access (e.g. sandboxed agents behind a
# restrictive proxy) can still run every other Stage 1 check; only
# check_validate_data_contracts.ps1 is skipped (not silently passed) below.
$yamlAvailable = $true
if (-not (Get-Command ConvertFrom-Yaml -ErrorAction SilentlyContinue)) {
  try {
    Import-Module powershell-yaml -ErrorAction Stop
  } catch {
    $yamlAvailable = $false
    Write-Warning "powershell-yaml unavailable ($($_.Exception.Message)) -- check_validate_data_contracts.ps1 will be SKIPPED, not passed. Install via: Install-Module powershell-yaml -Scope CurrentUser"
  }
}

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
  @{ Path = "tooling/validation/check_forbidden_content.ps1"; Args = @("-Root", $rootPath, "-FailOnError") },
  @{ Path = "tooling/validation/check_validate_data_contracts.ps1"; Args = @("-Root", $rootPath, "-FailOnError") },
  @{ Path = "tooling/validation/check_registry_builder.ps1"; Args = @("-Root", $rootPath, "-FailOnError") },
  @{ Path = "tooling/validation/check_measure_aggregation_methods.ps1"; Args = @("-Root", $rootPath) },
  @{ Path = "tooling/validation/check_data_contract_kpi_coverage.ps1"; Args = @("-Root", $rootPath, "-FailOnError") },
  @{ Path = "tooling/validation/check_usecase_page_types.ps1"; Args = @("-Root", $rootPath, "-FailOnError") },
  @{ Path = "tooling/validation/check_semantic_model_status.ps1"; Args = @("-Root", $rootPath) },
  @{ Path = "tooling/validation/check_markdownlint.ps1"; Args = @("-Root", $rootPath, "-FailOnError") }
)

# Python-based checks (cross-platform, invoked separately)
$pythonChecks = @(
  @{ Script = "tooling/validation/check_catalog_tmdl_drift.py"; Args = @("--repo-root", $rootPath) },
  @{ Script = "tooling/validation/check_docs_links.py"; Args = @("--repo-root", $rootPath) },
  @{ Script = "tooling/generator/validation/check_action_outcome_reconciliation.py"; Args = @("--strict") },
  @{ Script = "tooling/generator/validation/check_business_cases.py"; Args = @("--strict", "--repo-root", $rootPath) },
  # Layout-System-Boden (L4): jede analytische Absicht muss im Pflichtziel Power BI
  # eine Darstellung haben; Zweit-Konnektoren werden berichtet, blocken aber nicht,
  # solange sie im Aufbau sind. Kein eigener Checker — die Visual-Library hat eine
  # CLI, und die wird erweitert statt dupliziert.
  @{ Script = "tooling/superversion/layer_tools/visual_library.py"; Args = @("check-floor") },
  # Design-Tokens (L5): die DTCG-Fassung ist ERZEUGT — dieser Check faellt, sobald sie
  # von den YAML-Quellen abweicht. Ohne ihn waere das Interchange-Format still veraltet.
  @{ Script = "tooling/superversion/layer_tools/design_tokens.py"; Args = @() }
)

$resultsDir = Join-Path -Path $rootPath -ChildPath "tooling\validation\results"
$runsDir = Join-Path -Path $rootPath -ChildPath "internal\metrics\runs"
if (-not (Test-Path $resultsDir)) { New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null }
if (-not (Test-Path $runsDir)) { New-Item -ItemType Directory -Path $runsDir -Force | Out-Null }

$checkResults = @()
$overallStatus = "pass"

foreach ($check in $checks) {
  if ($check.Path -eq "tooling/validation/check_validate_data_contracts.ps1" -and -not $yamlAvailable) {
    Write-Host "SKIP $($check.Path) (powershell-yaml unavailable in this environment)" -ForegroundColor Yellow
    $checkResults += @{ check = $check.Path; status = "skipped"; exit_code = $null }
    continue
  }
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
    $json = $resultsPayload | ConvertTo-Json -Depth 4
    $json | Out-File -FilePath (Join-Path $resultsDir "latest_results.json") -Encoding utf8
    $timestampFile = (Get-Date -Format "yyyy-MM-dd_HHmm") + "_stage1.json"
    $json | Out-File -FilePath (Join-Path $runsDir $timestampFile) -Encoding utf8
    exit $exitCode
  }
  Write-Host "OK $($check.Path)"
}

# Run Python checks — prefer py launcher (avoids Windows Store alias for 'python')
$pythonExe = $null
foreach ($cmd in @("py -3", "python3", "python")) {
  try {
    $parts = $cmd -split " "
    $exe   = $parts[0]
    $xargs = @()
    if ($parts.Count -gt 1) { $xargs = @($parts[1..($parts.Count - 1)]) }
    $xargs += "--version"
    $ver   = (& $exe $xargs 2>&1) -join " "
    if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3") { $pythonExe = $cmd; break }
  } catch { continue }
}
if ($pythonExe) {
  foreach ($pyCheck in $pythonChecks) {
    $script = Join-Path $rootPath $pyCheck.Script
    if (-not (Test-Path $script)) { Write-Warning "Python check not found: $($pyCheck.Script)"; continue }
    Write-Host "START $($pyCheck.Script)"
    $parts   = $pythonExe -split " "
    $exe     = $parts[0]
    $xargs   = @()
    if ($parts.Count -gt 1) { $xargs = @($parts[1..($parts.Count - 1)]) }
    $xargs  += @($script) + $pyCheck.Args
    & $exe $xargs
    $exitCode = $LASTEXITCODE
    $status = if ($exitCode -eq 0) { "pass" } else { "fail" }
    $checkResults += @{ check = $pyCheck.Script; status = $status; exit_code = $exitCode }
    if ($exitCode -ne 0) {
      Write-Host "FAIL $($pyCheck.Script) ($exitCode)"
      $overallStatus = "fail"
    } else {
      Write-Host "OK $($pyCheck.Script)"
    }
  }
} else {
  Write-Warning "Python 3 not found; skipping Python checks."
}

# Write results regardless of outcome so diagnostics are always available
$resultsPayload = @{
  timestamp = (Get-Date -Format "o")
  stage = "stage1"
  overall_status = $overallStatus
  checks = $checkResults
}
$json = $resultsPayload | ConvertTo-Json -Depth 4
$json | Out-File -FilePath (Join-Path $resultsDir "latest_results.json") -Encoding utf8
$timestampFile = (Get-Date -Format "yyyy-MM-dd_HHmm") + "_stage1.json"
$json | Out-File -FilePath (Join-Path $runsDir $timestampFile) -Encoding utf8

if ($overallStatus -eq "fail") {
  Write-Host "Stage 1 FAILED. Results written to tooling/validation/results/latest_results.json and internal/metrics/runs/$timestampFile" -ForegroundColor Red
  exit 1
}

Write-Host "Stage 1 checks passed. Results written to tooling/validation/results/latest_results.json and internal/metrics/runs/$timestampFile" -ForegroundColor Green
exit 0
