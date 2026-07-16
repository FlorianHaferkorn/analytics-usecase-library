<#
.SYNOPSIS
  DEPRECATED (R3.4, 2026-07-09): Optional audit of a .Report folder using
  pbi-cli (MinaSaad1/pbi-cli-tool).
.DESCRIPTION
  Superseded by fab-inspector (check_fab_inspector.ps1, wired into
  run_fabric_checks.ps1 since R3.2): fab-inspector is open source,
  cross-platform, actually CI-wired and verified, whereas this script was
  never invoked by run_fabric_checks.ps1 or any CI workflow, required a
  manual `pipx install pbi-cli-tool` + Power BI Desktop connection for full
  functionality, and always skipped gracefully in every CI run to date. Not
  deleted (still callable for ad-hoc manual comparison) -- see
  internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md for the R3.4 decision.

  Runs a set of read-only pbi-cli commands against a generated .Report folder
  and compares findings with our own check_pbir_schema.ps1 validator.

  This check is OPTIONAL. It requires:
    - pbi-cli-tool installed: pipx install pbi-cli-tool
    - For Desktop/semantic-model operations: Power BI Desktop running + pbi connect

  In CI the check is skipped gracefully when pbi is unavailable.
  Set ENABLE_PBI_CLI_CHECKS=1 to force the check (useful for local development).

  pbi-cli MIT license (own code) + separate Microsoft DLL terms for Desktop ops.
  Source: https://github.com/MinaSaad1/pbi-cli

.PARAMETER ReportPath
  Path to the .Report folder to audit.
.PARAMETER SkipIfMissing
  Silently skip (exit 0) when pbi is not installed. Default: true.
.EXAMPLE
  .\check_with_pbi_cli.ps1 -ReportPath "products/fabric/powerbi/dist/COM-001_Sales_Performance.Report"
#>
Param(
    [string]$ReportPath   = "",
    [switch]$SkipIfMissing = $true
)

$ErrorActionPreference = "Stop"

# ── Check whether pbi-cli is available ────────────────────────────────────────
$pbiAvailable = $false
try {
    $ver = (& pbi --version 2>&1) -join ""
    if ($LASTEXITCODE -eq 0) { $pbiAvailable = $true }
} catch { }

if (-not $pbiAvailable) {
    $envOverride = [System.Environment]::GetEnvironmentVariable("ENABLE_PBI_CLI_CHECKS")
    if ($envOverride -eq "1") {
        Write-Error "ENABLE_PBI_CLI_CHECKS=1 but pbi is not installed. Install: pipx install pbi-cli-tool"
        exit 1
    }
    if ($SkipIfMissing) {
        Write-Host "pbi-cli not found — skipping optional check. Install with: pipx install pbi-cli-tool" -ForegroundColor DarkGray
        exit 0
    }
    Write-Error "pbi-cli not found and -SkipIfMissing is false."
    exit 1
}

# ── Resolve ReportPath ────────────────────────────────────────────────────────
$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot  = (Get-Item $scriptDir).Parent.Parent.Parent.Parent.FullName

if (-not $ReportPath) {
    $distDir = Join-Path $repoRoot "products/fabric/powerbi/dist"
    $first   = Get-ChildItem -Path $distDir -Filter "*.Report" -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $first) { Write-Host "No .Report found — skipping pbi-cli check." -ForegroundColor DarkGray; exit 0 }
    $ReportPath = $first.FullName
}

$ReportPath = if ([System.IO.Path]::IsPathRooted($ReportPath)) { $ReportPath } else { Join-Path $repoRoot $ReportPath }
if (-not (Test-Path $ReportPath)) { Write-Error "Report path not found: $ReportPath"; exit 1 }

Write-Host ">> pbi-cli audit: $ReportPath" -ForegroundColor Cyan

$failed = 0

# ── pbi report info ───────────────────────────────────────────────────────────
Write-Host "  pbi --json report info ..." -NoNewline
$infoJson = & pbi --json report info --report $ReportPath 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host " FAIL" -ForegroundColor Red
    Write-Warning "pbi report info failed (exit $LASTEXITCODE). Output: $infoJson"
    $failed++
} else {
    Write-Host " OK" -ForegroundColor Green
    try {
        $info = $infoJson | ConvertFrom-Json
        $pageCount = if ($info.pages) { $info.pages.Count } else { "?" }
        Write-Host "    pages=$pageCount"
    } catch { }
}

# ── pbi report validate ───────────────────────────────────────────────────────
Write-Host "  pbi --json report validate ..." -NoNewline
$validateJson = & pbi --json report validate --report $ReportPath 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host " FAIL" -ForegroundColor Red
    Write-Warning "pbi report validate failed. Output: $validateJson"
    $failed++
} else {
    Write-Host " OK" -ForegroundColor Green
    try {
        $result = $validateJson | ConvertFrom-Json
        $errors = if ($result.errors) { $result.errors } else { @() }
        if ($errors.Count -gt 0) {
            Write-Host "    Validation findings ($($errors.Count)):" -ForegroundColor Yellow
            $errors | ForEach-Object { Write-Host "      - $_" -ForegroundColor Yellow }
        } else {
            Write-Host "    No validation errors." -ForegroundColor Green
        }
    } catch { }
}

# ── pbi visual list ───────────────────────────────────────────────────────────
Write-Host "  pbi --json visual list ..." -NoNewline
$visualsJson = & pbi --json visual list --report $ReportPath 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host " FAIL" -ForegroundColor Red
    $failed++
} else {
    Write-Host " OK" -ForegroundColor Green
    try {
        $visuals = $visualsJson | ConvertFrom-Json
        $count   = if ($visuals -is [array]) { $visuals.Count } else { "?" }
        Write-Host "    visuals=$count"
    } catch { }
}

# ── Summary ───────────────────────────────────────────────────────────────────
if ($failed -gt 0) {
    Write-Host "pbi-cli check: $failed step(s) failed." -ForegroundColor Red
    Write-Host "Note: pbi-cli findings are supplementary. Our own check_pbir_schema.ps1 is the CI authority." -ForegroundColor DarkGray
    exit 1
}
Write-Host "pbi-cli check passed." -ForegroundColor Green
exit 0
