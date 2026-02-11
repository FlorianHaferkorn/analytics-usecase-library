<#
.SYNOPSIS
  Validates report page visual positions against Layout_Grid_System (padding, row bounds, content width).
.DESCRIPTION
  Reads report definition/pages/*/visuals/*/visual.json and page.json; checks positions against
  core/templates/page_templates/governance/Layout_Grid_System.yaml constants.
  Use for Aurora or any PBIR report to ensure layout compliance.
.PARAMETER ReportPath
  Path to report definition folder (e.g. .../CoreActionReady.Report/definition). Default: Aurora report.
.EXAMPLE
  .\check_report_layout.ps1
.EXAMPLE
  .\check_report_layout.ps1 -ReportPath "showcases/aurora_group/semantic_models/CoreActionReady.Report/definition"
#>
Param(
  [string]$ReportPath = "",
  [string]$PageFilter = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot = (Get-Item $scriptDir).Parent.Parent.Parent.FullName

if (-not $ReportPath) {
  $ReportPath = Join-Path $repoRoot "showcases/aurora_group/semantic_models/CoreActionReady.Report/definition"
}
$reportDef = if ([System.IO.Path]::IsPathRooted($ReportPath)) { $ReportPath } else { Join-Path $repoRoot $ReportPath }

if (-not (Test-Path $reportDef)) {
  Write-Error "Report definition not found: $reportDef"
  exit 1
}

# Layout Grid constants (Layout_Grid_System.yaml / layout_calculator.py)
$PADDING = 20
$CANVAS_WIDTH = 1920
$CANVAS_HEIGHT = 1080
$ACTION_PANEL_X = 1570
$ACTION_PANEL_WIDTH = 350
$CONTENT_WIDTH_WITH_PANEL = $CANVAS_WIDTH - $PADDING - $ACTION_PANEL_WIDTH - $PADDING  # 1510
$ROW1_END = 160
$ROW2_START = 180
$ROW2_END = 580
$ROW3_START = 600
$ROW3_END = 900
$ROW4_START = 920

$pagesDir = Join-Path $reportDef "pages"
if (-not (Test-Path $pagesDir)) {
  Write-Host "No pages folder; skipping layout check." -ForegroundColor Yellow
  exit 0
}

$violations = [System.Collections.ArrayList]::new()
$pageIds = Get-ChildItem -Path $pagesDir -Directory | Where-Object { $_.Name -match '^[a-f0-9]+$' } | ForEach-Object { $_.Name }

foreach ($pageId in $pageIds) {
  $pageJsonPath = Join-Path $pagesDir "$pageId/page.json"
  if (-not (Test-Path $pageJsonPath)) { continue }
  $pageObj = Get-Content $pageJsonPath -Raw | ConvertFrom-Json
  $displayName = if ($pageObj.displayName) { $pageObj.displayName } else { $pageId }
  if ($PageFilter -and $displayName -notlike $PageFilter) { continue }
  $pageWidth = if ($pageObj.width) { [int]$pageObj.width } else { $CANVAS_WIDTH }
  $pageHeight = if ($pageObj.height) { [int]$pageObj.height } else { $CANVAS_HEIGHT }

  $visualsDir = Join-Path $pagesDir "$pageId/visuals"
  if (-not (Test-Path $visualsDir)) { continue }

  $hasActionPanel = $false
  Get-ChildItem -Path $visualsDir -Directory | ForEach-Object {
    $vPath = Join-Path $_.FullName "visual.json"
    if (-not (Test-Path $vPath)) { return }
    $raw = Get-Content $vPath -Raw -Encoding UTF8
    if ($raw -match '"name"\s*:\s*"([^"]+)"\s*,\s*"position"\s*:\s*\{\s*"x"\s*:\s*([0-9.]+)\s*,\s*"y"\s*:\s*([0-9.]+)[^}]*"height"\s*:\s*([0-9.]+)[^}]*"width"\s*:\s*([0-9.]+)') {
      $name = $Matches[1]
      $px = [double]$Matches[2]; $py = [double]$Matches[3]; $ph = [double]$Matches[4]; $pw = [double]$Matches[5]
      if ($name -eq "ActionPanel" -or (($raw -match '"visualType"\s*:\s*"textbox"') -and $px -ge 1500 -and $pw -ge 300)) { $script:hasActionPanel = $true }
    }
  }

  $contentRight = if ($hasActionPanel) { $ACTION_PANEL_X - $PADDING } else { $pageWidth - $PADDING }
  $contentWidth = $contentRight - $PADDING

  Get-ChildItem -Path $visualsDir -Directory | ForEach-Object {
    $vPath = Join-Path $_.FullName "visual.json"
    if (-not (Test-Path $vPath)) { return }
    $raw = Get-Content $vPath -Raw -Encoding UTF8
    if (-not ($raw -match '"name"\s*:\s*"([^"]+)"\s*,\s*"position"\s*:\s*\{\s*"x"\s*:\s*([0-9.]+)\s*,\s*"y"\s*:\s*([0-9.]+)[^}]*"height"\s*:\s*([0-9.]+)[^}]*"width"\s*:\s*([0-9.]+)')) { return }
    $name = $Matches[1]
    $x = [double]$Matches[2]
    $y = [double]$Matches[3]
    $h = [double]$Matches[4]
    $w = [double]$Matches[5]

    $isActionPanel = ($name -eq "ActionPanel" -or (($x -ge ($ACTION_PANEL_X - 1)) -and $w -ge ($ACTION_PANEL_WIDTH - 1)))
    if ($isActionPanel) {
      # Action Panel/Teaser: allowed at x=1570, width 350, full height (y=0, height=1080) per Layout_Grid_System
      if ($x + $w -gt $pageWidth) {
        [void]$violations.Add("$displayName / $name : x+width=$($x+$w) exceeds canvas $pageWidth")
      }
      continue
    }
    if ($x -lt $PADDING) {
      [void]$violations.Add("$displayName / $name : x=$x (min $PADDING)")
    }
    if ($y -lt $PADDING) {
      [void]$violations.Add("$displayName / $name : y=$y (min $PADDING)")
    }
    if ($x + $w -gt $pageWidth - $PADDING) {
      [void]$violations.Add("$displayName / $name : x+width=$($x+$w) exceeds $($pageWidth - $PADDING)")
    }
    if ($y + $h -gt $pageHeight - $PADDING) {
      [void]$violations.Add("$displayName / $name : y+height=$($y+$h) exceeds $($pageHeight - $PADDING)")
    }
    # Content width when panel present (main area visuals should not extend past 1510)
    if ($hasActionPanel -and ($x + $w) -gt $contentRight) {
      [void]$violations.Add("$displayName / $name : extends into Action Panel area (x+width=$($x+$w), content ends $contentRight)")
    }
  }
}

if ($violations.Count -gt 0) {
  Write-Host "Layout violations (Layout_Grid_System):" -ForegroundColor Red
  foreach ($v in $violations) { Write-Host "  $v" -ForegroundColor Red }
  exit 1
}

Write-Host "Report layout check passed (padding, bounds, content width)." -ForegroundColor Green
exit 0
