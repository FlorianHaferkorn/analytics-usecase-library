<#
.SYNOPSIS
  R4.1 Bridge-Workflow: one-shot Power BI Desktop Bridge screenshot capture for
  the visual close-loop (structural validation alone does not prove a report
  renders correctly -- see UMSETZUNGSPLAN_REPORT_EXZELLENZ.md Cut C4).

.DESCRIPTION
  MAINTAINER-ONLY. The Power BI Desktop Bridge is a local-only, named-pipe IPC
  server hosted inside the Desktop process (Preview) -- there is no remote
  access, so this cannot run in CI, a sandbox, or any headless agent
  environment. It requires:
    - Windows, with Power BI Desktop installed and running
    - Desktop's "Enable external tool access to Power BI Desktop through
      secure local APIs" preview feature turned on (File > Options and
      Settings > Options > Preview Features)
    - Node.js 20+ (for @microsoft/powerbi-desktop-bridge-cli)

  Wraps the official `powerbi-desktop` CLI (npm package
  @microsoft/powerbi-desktop-bridge-cli) per Microsoft's own documented
  workflow (open -> status -> reload -> screenshot-all):
    https://learn.microsoft.com/power-bi/developer/agentic/power-bi-desktop-bridge-overview
    https://github.com/microsoft/skills-for-fabric/blob/main/skills/powerbi-report-authoring/SKILL.md

  Every command this script runs is copied verbatim from those two official
  sources -- nothing here is guessed. What IS unverified: this script itself
  has never been executed (no Windows/Desktop available in the environment
  that authored it). The first real run is the maintainer's job -- see
  products/fabric/powerbi/docs/references/desktop-bridge-screenshot-workflow.md
  for the full writeup, prerequisites, and troubleshooting.

.PARAMETER PbipPath
  Path to the .Report (or its .pbip) to open and screenshot, e.g.
  "products/fabric/powerbi/dist/COM-002_Margin_Price_Performance.Report".
.PARAMETER OutputDir
  Folder to write PNG screenshots into. Default:
  internal/metrics/desktop_screenshots/<ReportName>/<timestamp>/ (gitignored --
  attach/paste the proof screenshot into the PR or ledger entry, don't commit
  the PNG itself).
.PARAMETER ProcessId
  Desktop instance PID to target. If omitted, the script runs
  `powerbi-desktop status`, prints it, and asks you to enter the PID
  interactively -- the exact status output shape is not verified from this
  session, so this script does not attempt to auto-parse it.
.PARAMETER WaitSeconds
  Passed to `powerbi-desktop reload --wait-seconds` and used as the initial
  post-`open` load wait. Default 60.
.EXAMPLE
  # One-liner, from repo root, on the maintainer's Windows workstation:
  .\products\fabric\powerbi\tooling\desktop_bridge_screenshot.ps1 `
    -PbipPath "products\fabric\powerbi\dist\COM-002_Margin_Price_Performance.Report"
#>
Param(
    [Parameter(Mandatory = $true)]
    [string]$PbipPath,
    [string]$OutputDir = "",
    [int]$ProcessId = 0,
    [int]$WaitSeconds = 60
)

$ErrorActionPreference = "Stop"

if ($IsWindows -eq $false) {
    Write-Error "The Power BI Desktop Bridge is Windows-only (local named-pipe IPC inside the Desktop process, no remote access). Run this script on a Windows workstation with Power BI Desktop installed, not in CI or a sandbox."
    exit 1
}

$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot = (Get-Item $scriptDir).Parent.Parent.Parent.Parent.FullName

if (-not [System.IO.Path]::IsPathRooted($PbipPath)) {
    $PbipPath = Join-Path $repoRoot $PbipPath
}
if (-not (Test-Path $PbipPath)) {
    Write-Error "Path not found: $PbipPath"
    exit 1
}

$reportName = (Get-Item $PbipPath).BaseName
if (-not $OutputDir) {
    $timestamp = Get-Date -Format "yyyy-MM-dd_HHmm"
    $OutputDir = Join-Path $repoRoot "internal/metrics/desktop_screenshots/$reportName/$timestamp"
} elseif (-not [System.IO.Path]::IsPathRooted($OutputDir)) {
    $OutputDir = Join-Path $repoRoot $OutputDir
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# ── 1. Ensure the bridge CLI is installed ─────────────────────────────────
$cli = Get-Command powerbi-desktop -ErrorAction SilentlyContinue
if (-not $cli) {
    $node = Get-Command node -ErrorAction SilentlyContinue
    if (-not $node) {
        Write-Error "Node.js not found. Install Node.js 20+ first (required by @microsoft/powerbi-desktop-bridge-cli)."
        exit 1
    }
    Write-Host "Installing @microsoft/powerbi-desktop-bridge-cli (one-time)..." -ForegroundColor Cyan
    npm install -g "@microsoft/powerbi-desktop-bridge-cli@latest"
    $cli = Get-Command powerbi-desktop -ErrorAction SilentlyContinue
    if (-not $cli) {
        Write-Error "powerbi-desktop still not found on PATH after install. Open a new shell (PATH refresh) and retry."
        exit 1
    }
}

# ── 2. Open the report in Desktop ──────────────────────────────────────────
Write-Host ">> powerbi-desktop open `"$PbipPath`"" -ForegroundColor Cyan
& powerbi-desktop open "$PbipPath"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "powerbi-desktop open returned exit $LASTEXITCODE -- Desktop may already have this report open. Continuing."
}
Write-Host "Waiting for Power BI Desktop to finish loading (up to $([Math]::Min($WaitSeconds, 30))s)..." -ForegroundColor DarkGray
Start-Sleep -Seconds ([Math]::Min($WaitSeconds, 30))

# ── 3. Resolve the target Desktop instance PID ─────────────────────────────
if ($ProcessId -le 0) {
    Write-Host ">> powerbi-desktop status" -ForegroundColor Cyan
    & powerbi-desktop status
    Write-Host ""
    $ProcessId = [int](Read-Host "Enter the PID for '$reportName' from the status output above")
}

# ── 4. Reload (apply on-disk PBIR state) then screenshot every page ───────
Write-Host ">> powerbi-desktop reload --pid $ProcessId --wait-seconds $WaitSeconds" -ForegroundColor Cyan
& powerbi-desktop reload --pid $ProcessId --wait-seconds $WaitSeconds
if ($LASTEXITCODE -ne 0) {
    Write-Error "reload failed (exit $LASTEXITCODE). See docs/references/desktop-bridge-screenshot-workflow.md#troubleshooting."
    exit $LASTEXITCODE
}

Write-Host ">> powerbi-desktop screenshot-all --pid $ProcessId --output-dir `"$OutputDir`"" -ForegroundColor Cyan
& powerbi-desktop screenshot-all --pid $ProcessId --output-dir "$OutputDir"
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "Screenshots written to: $OutputDir" -ForegroundColor Green
    Get-ChildItem -Path $OutputDir -Filter "*.png" -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  $($_.Name)" }
} else {
    Write-Host "screenshot-all failed (exit $exitCode). See docs/references/desktop-bridge-screenshot-workflow.md#troubleshooting." -ForegroundColor Red
}
exit $exitCode
