<#
.SYNOPSIS
  Runs fab-inspector (formerly PBI-Inspector V2) custom JSON-Logic BPA rules
  against every generated .Report folder.
.DESCRIPTION
  fab-inspector (https://github.com/NatVanG/fab-inspector, MIT) is a
  cross-platform, PBIR-capable rules engine. This script runs our own rule
  set (fab-inspector-rules.json: max visuals/page, no vertical scroll,
  theme-colour hygiene) against products/fabric/powerbi/dist and writes a
  JSON report per .Report folder for CI artifact upload.

  Resolution order for the binary:
    1. $env:FAB_INSPECTOR_EXE (set by CI after downloading the pinned release)
    2. `fab-inspector` / `fab-inspector.exe` on PATH (local dev install)
    3. .tools/fab-inspector/**/*.exe (local manual install, mirrors pbi-tools)

  In CI the binary is installed explicitly (see .github/workflows/stage1.yml
  and .tools/fab-inspector.lock), so this check runs for real there. Locally,
  when the binary is unavailable, the check is skipped gracefully (exit 0)
  unless ENABLE_FAB_INSPECTOR_CHECKS=1 forces it.

  See docs/architecture/r3-2-fab-inspector-integration.md for the tool
  selection rationale and why the three rules are safe to run as logType:error.
.PARAMETER DistRoot
  Path to the dist folder containing .Report directories.
.PARAMETER RulesPath
  Path to the fab-inspector JSON-Logic rules file.
.PARAMETER OutputRoot
  Directory to write per-report JSON results into (CI artifact source).
.EXAMPLE
  .\check_fab_inspector.ps1 -DistRoot "products/fabric/powerbi/dist"
#>
Param(
    [string]$DistRoot    = "products/fabric/powerbi/dist",
    [string]$RulesPath   = "",
    [string]$OutputRoot  = "internal/metrics/runs/fab_inspector",
    [switch]$SkipIfMissing = $true
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot  = (Get-Item $scriptDir).Parent.Parent.Parent.Parent.FullName

if (-not $RulesPath) {
    $RulesPath = Join-Path $scriptDir "fab-inspector-rules.json"
}
$RulesPath = if ([System.IO.Path]::IsPathRooted($RulesPath)) { $RulesPath } else { Join-Path $repoRoot $RulesPath }
$DistRoot  = if ([System.IO.Path]::IsPathRooted($DistRoot)) { $DistRoot } else { Join-Path $repoRoot $DistRoot }
$OutputRoot = if ([System.IO.Path]::IsPathRooted($OutputRoot)) { $OutputRoot } else { Join-Path $repoRoot $OutputRoot }

# ── Resolve the fab-inspector binary ──────────────────────────────────────────
function Resolve-FabInspectorExe {
    if ($env:FAB_INSPECTOR_EXE -and (Test-Path $env:FAB_INSPECTOR_EXE)) {
        return $env:FAB_INSPECTOR_EXE
    }
    $onPath = Get-Command fab-inspector -ErrorAction SilentlyContinue
    if ($onPath) { return $onPath.Source }
    $localToolsDir = Join-Path $repoRoot ".tools/fab-inspector"
    if (Test-Path $localToolsDir) {
        $candidate = Get-ChildItem -Path $localToolsDir -Recurse -Filter "*.exe" -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match "(?i)fab-?insp" } |
            Select-Object -First 1
        if (-not $candidate) {
            $candidate = Get-ChildItem -Path $localToolsDir -Recurse -File -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -match "(?i)^fab-inspector$" } |
                Select-Object -First 1
        }
        if ($candidate) { return $candidate.FullName }
    }
    return $null
}

$fabInspectorExe = Resolve-FabInspectorExe

if (-not $fabInspectorExe) {
    $envOverride = [System.Environment]::GetEnvironmentVariable("ENABLE_FAB_INSPECTOR_CHECKS")
    if ($envOverride -eq "1") {
        Write-Error "ENABLE_FAB_INSPECTOR_CHECKS=1 but fab-inspector was not found. See .tools/README.md."
        exit 1
    }
    if ($SkipIfMissing) {
        Write-Host "fab-inspector not found -- skipping BPA rule check. See .tools/README.md to install." -ForegroundColor DarkGray
        exit 0
    }
    Write-Error "fab-inspector not found and -SkipIfMissing is false."
    exit 1
}

if (-not (Test-Path $DistRoot)) {
    Write-Error "Dist root not found: $DistRoot"
    exit 1
}
if (-not (Test-Path $RulesPath)) {
    Write-Error "Rules file not found: $RulesPath"
    exit 1
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

$reportDirs = Get-ChildItem -Path $DistRoot -Filter "*.Report" -Directory -ErrorAction SilentlyContinue
if (-not $reportDirs) {
    Write-Host "No .Report directories found in $DistRoot" -ForegroundColor Yellow
    exit 0
}

Write-Host ">> fab-inspector BPA rules ($($reportDirs.Count) report(s), $fabInspectorExe)" -ForegroundColor Cyan

$failed = 0
foreach ($rDir in $reportDirs) {
    $reportOutput = Join-Path $OutputRoot $rDir.BaseName
    New-Item -ItemType Directory -Force -Path $reportOutput | Out-Null

    Write-Host "   $($rDir.Name)" -ForegroundColor DarkGray
    & $fabInspectorExe -fabricitem $rDir.FullName -rules $RulesPath -output $reportOutput -formats "Console,JSON" -verbose false 2>&1 |
        ForEach-Object { Write-Host "     $_" }

    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
        $failed++
        Write-Host "     FAIL (exit $LASTEXITCODE)" -ForegroundColor Red
    }
}

Write-Host ""
if ($failed -gt 0) {
    Write-Host "fab-inspector BPA rules: $failed report(s) failed. Results: $OutputRoot" -ForegroundColor Red
    exit 1
}
Write-Host "fab-inspector BPA rules passed. Results: $OutputRoot" -ForegroundColor Green
exit 0
