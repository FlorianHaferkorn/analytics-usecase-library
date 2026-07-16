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
  workflow (open -> status -> screenshot per page):
    https://learn.microsoft.com/power-bi/developer/agentic/power-bi-desktop-bridge-overview
    https://github.com/microsoft/skills-for-fabric/blob/main/skills/powerbi-report-authoring/SKILL.md

  Deliberately does NOT use `reload` or `screenshot-all` (Microsoft's own
  documented order), because both depend on the CLI's resolveReportDir(),
  which only finds a SIBLING `<Name>.Report` folder next to a `.pbip` -- it
  never checks whether the `.pbip`'s own parent directory IS the `.Report`
  folder. This repo's documented PBIP layout (PBIP_REPORT_STRUCTURE.md)
  nests `Report.pbip` INSIDE `<UseCase>.Report/`, so resolveReportDir always
  returns null here and both commands fail with `REPORT_DIR_REQUIRED` --
  confirmed against the shipped CLI source (dist/index.js), not a bug on our
  side, and there is no flag to override it. The singular `screenshot
  <page-id>` command never calls resolveReportDir (it targets a page id +
  `--pid` directly), so this script reads page ids from the report's own
  `definition/pages/pages.json` and screenshots each one individually.
  Practical effect: `open` already loads the current on-disk state, so
  skipping `reload` only matters if you edited PBIR locally after Desktop
  was already running against this report -- close and reopen Desktop for
  it in that case, since reload cannot be made to work with this layout.

  Every command this script runs is copied verbatim from the official
  sources above, or read directly from the shipped CLI source where the
  docs don't cover it -- nothing here is guessed. See
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
  Passed to each `powerbi-desktop screenshot --wait-seconds` call and used as
  the initial post-`open` load wait. Default 60.
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

# ── 1b. Point the bridge CLI at a Microsoft Store install, if present ─────
# The CLI's own executable auto-discovery (dist/index.js, findDesktopExecutable)
# only checks traditional MSI/EXE install roots (Program Files, WindowsApps\..
# without a package-family suffix) -- it never checks the real Microsoft Store
# package path pattern below, so Store installs fail with "Power BI Desktop
# executable was not found" even though Desktop is installed and running. The
# CLI honors $env:PBI_DESKTOP_PATH first, before its own auto-discovery
# (confirmed by inspecting the shipped package source, not documented in the
# public docs) -- so pre-populating it here fixes Store installs without
# requiring the maintainer to find and set it by hand every run.
if (-not $env:PBI_DESKTOP_PATH) {
    $storeCandidate = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WindowsApps" `
        -Filter "Microsoft.MicrosoftPowerBIDesktop_*" -Directory -ErrorAction SilentlyContinue |
        ForEach-Object { Join-Path $_.FullName "bin\PBIDesktop.exe" } |
        Where-Object { Test-Path $_ } |
        Select-Object -First 1
    if ($storeCandidate) {
        Write-Host "Detected Microsoft Store Power BI Desktop install: $storeCandidate" -ForegroundColor DarkGray
        $env:PBI_DESKTOP_PATH = $storeCandidate
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

# ── 4. Resolve the report's own page ids from its local pages.json ────────
# No reload step: see .DESCRIPTION for why reload/screenshot-all cannot work
# with this repo's PBIP layout, and why skipping reload is safe for a
# just-`open`-ed report.
$reportDir = if ((Get-Item $PbipPath).PSIsContainer) { $PbipPath } else { Split-Path -Parent $PbipPath }
$pagesJsonPath = Join-Path $reportDir "definition/pages/pages.json"
if (-not (Test-Path $pagesJsonPath)) {
    Write-Error "pages.json not found at $pagesJsonPath -- cannot enumerate pages to screenshot."
    exit 1
}
$pageIds = @((Get-Content -Path $pagesJsonPath -Raw | ConvertFrom-Json).pageOrder)
if (-not $pageIds -or $pageIds.Count -eq 0) {
    Write-Error "No pages found in $pagesJsonPath (pageOrder empty)."
    exit 1
}
Write-Host "Pages to screenshot: $($pageIds -join ', ')" -ForegroundColor DarkGray

# ── 5. Screenshot each page individually ───────────────────────────────────
$failures = 0
foreach ($pageId in $pageIds) {
    $outFile = Join-Path $OutputDir "$pageId.png"
    Write-Host ">> powerbi-desktop screenshot $pageId --pid $ProcessId --output `"$outFile`" --wait-seconds $WaitSeconds" -ForegroundColor Cyan
    & powerbi-desktop screenshot $pageId --pid $ProcessId --output "$outFile" --wait-seconds $WaitSeconds
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FAILED (exit $LASTEXITCODE) for page $pageId" -ForegroundColor Red
        $failures++
    }
}

if ($failures -eq 0) {
    Write-Host ""
    Write-Host "Screenshots written to: $OutputDir" -ForegroundColor Green
    Get-ChildItem -Path $OutputDir -Filter "*.png" -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  $($_.Name)" }
    exit 0
} else {
    Write-Host "$failures of $($pageIds.Count) page screenshot(s) failed. See docs/references/desktop-bridge-screenshot-workflow.md#troubleshooting." -ForegroundColor Red
    exit 1
}
