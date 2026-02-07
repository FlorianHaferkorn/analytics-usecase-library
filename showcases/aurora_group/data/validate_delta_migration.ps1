<#
.SYNOPSIS
  Validates Aurora gold fact tables: optional regeneration, format coverage check, optional Stage 1.
.DESCRIPTION
  Ensures date-partitioned facts are written as Delta Lake where expected. Run from repository root.
  Optionally regenerates gold data, runs check_fact_coverage.py, and Stage 1 checks.
.EXAMPLE
  .\showcases\aurora_group\data\validate_delta_migration.ps1
.EXAMPLE
  .\showcases\aurora_group\data\validate_delta_migration.ps1 -Regenerate -Domain experience
.EXAMPLE
  .\showcases\aurora_group\data\validate_delta_migration.ps1 -Regenerate -SkipStage1
#>
Param(
  [string]$Root = ".",
  [switch]$Regenerate,
  [string]$Domain = "",
  [switch]$SkipStage1
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
# Repo root: showcases/aurora_group/data -> go up 4 levels
$repoRoot = (Get-Item $scriptDir).Parent.Parent.Parent.Parent.FullName
if ($Root -and $Root -ne "." -and (Test-Path $Root)) {
  $repoRoot = (Resolve-Path $Root).Path
}
if (-not (Test-Path (Join-Path $repoRoot "framework"))) {
  Write-Error "Repository root not found (expected 'framework' under $repoRoot). Run from repo root or set -Root."
  exit 1
}

# Facts that should be Delta Lake (date-partitioned). Must match check_fact_coverage.py DELTA_EXPECTED_FACTS.
$deltaExpectedFacts = @(
  "fact_sales", "fact_accounts_payable", "fact_accounts_receivable", "fact_cash_position",
  "fact_cash_flow", "fact_inventory", "fact_cogs", "fact_fulfillment", "fact_stockout",
  "fact_forecast", "fact_ops", "fact_ops_failures", "fact_maintenance", "fact_quality",
  "fact_experience"
)

function Invoke-CoverageCheck {
  $goldDir = Join-Path $repoRoot "showcases\aurora_group\data\gold"
  $coverageScript = Join-Path $goldDir "check_fact_coverage.py"
  if (-not (Test-Path $coverageScript)) {
    Write-Error "check_fact_coverage.py not found: $coverageScript"
    exit 1
  }
  Push-Location $repoRoot
  try {
    $out = & python $coverageScript 2>&1
    $out
    return $out
  } finally {
    Pop-Location
  }
}

function Get-FactsWithWrongFormat {
  param([string[]]$CoverageOutput)
  $failures = @()
  foreach ($line in $CoverageOutput) {
    if ($line -notmatch '^\s*(fact_\w+)\s+') { continue }
    $factName = $Matches[1].Trim()
    if ($deltaExpectedFacts -notcontains $factName) { continue }
    $parts = ($line -split '\s{2,}')
    if ($parts.Count -lt 8) { continue }
    $format = $parts[7].Trim()
    if ($format -eq "Parquet") {
      $failures += $factName
    }
  }
  return $failures
}

# Optional regeneration
if ($Regenerate) {
  Write-Host "Regenerating Aurora gold data..." -ForegroundColor Cyan
  $genScript = Join-Path $repoRoot "showcases\aurora_group\data\scripts\generate_aurora_gold.py"
  if (-not (Test-Path $genScript)) {
    Write-Error "generate_aurora_gold.py not found: $genScript"
    exit 1
  }
  Push-Location $repoRoot
  try {
    if ($Domain) {
      & python $genScript --domain $Domain
    } else {
      & python $genScript
    }
    if ($LASTEXITCODE -ne 0) {
      Write-Error "Regeneration failed with exit code $LASTEXITCODE"
      exit $LASTEXITCODE
    }
  } finally {
    Pop-Location
  }
  Write-Host "Regeneration completed." -ForegroundColor Green
}

# Run fact coverage check
Write-Host "Running fact coverage check..." -ForegroundColor Cyan
$coverageOutput = Invoke-CoverageCheck
$wrongFormat = Get-FactsWithWrongFormat -CoverageOutput $coverageOutput

if ($wrongFormat.Count -gt 0) {
  Write-Host ""
  Write-Host "The following date-partitioned facts are Parquet but should be Delta:" -ForegroundColor Yellow
  $wrongFormat | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
  Write-Host "Install deltalake (pip install deltalake) and regenerate, or run: py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain <domain>" -ForegroundColor Gray
  exit 1
}

# Optional Stage 1
if (-not $SkipStage1) {
  Write-Host ""
  Write-Host "Running Stage 1 checks..." -ForegroundColor Cyan
  $stage1 = Join-Path $repoRoot "_internal\tools\run_stage1_checks.ps1"
  if (-not (Test-Path $stage1)) {
    Write-Warning "run_stage1_checks.ps1 not found; skipping Stage 1."
  } else {
    & $stage1 -Root $repoRoot
    if ($LASTEXITCODE -ne 0) {
      Write-Error "Stage 1 checks failed."
      exit $LASTEXITCODE
    }
  }
}

Write-Host ""
Write-Host "Delta migration validation passed." -ForegroundColor Green
