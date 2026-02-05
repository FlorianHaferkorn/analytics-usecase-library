<#
.SYNOPSIS
  Validates diagramLayout.json follows the spaghetti principle: _Measures top-left, facts horizontal at top, dims vertical on left.
.DESCRIPTION
  Ensures model view layout consistency: (1) _Measures at (0,0), (2) all fact tables in horizontal row at y=0 starting x=280,
  (3) all dimension tables in vertical column at x=0 starting y=120, (4) spacing approximately 250px (facts) and 120px (dims).
  Run from repository root. DistRoot can be a tables dir (e.g. .../definition/tables) or dist root.
.PARAMETER DistRoot
  Root path: either .../definition/tables (single semantic model) or implementations/microsoft_fabric_powerbi/dist (multiple).
#>
Param(
  [string]$DistRoot = "implementations/microsoft_fabric_powerbi/dist"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Location).Path
$rootResolved = if ([System.IO.Path]::IsPathRooted($DistRoot)) { $DistRoot } else { Join-Path $repoRoot ($DistRoot -replace '/', [System.IO.Path]::DirectorySeparatorChar) }

if (-not (Test-Path $rootResolved)) {
  Write-Host "DistRoot not found: $rootResolved. Skipping diagram layout check." -ForegroundColor Yellow
  exit 0
}

# Resolve semantic model root(s): find diagramLayout.json files
$semanticModelRoots = @()
if ((Get-Item $rootResolved).Name -eq "tables") {
  # If root is .../definition/tables, look for diagramLayout.json in semantic model root (two levels up)
  $defDir = (Resolve-Path (Join-Path $rootResolved "..")).Path
  $smRoot = (Resolve-Path (Join-Path $defDir "..")).Path
  if (Test-Path (Join-Path $smRoot "diagramLayout.json")) {
    $semanticModelRoots = @($smRoot)
  }
}
if ($semanticModelRoots.Count -eq 0) {
  # Find all diagramLayout.json files under root
  $layoutFiles = Get-ChildItem -Path $rootResolved -Recurse -Filter "diagramLayout.json" -ErrorAction SilentlyContinue
  foreach ($lf in $layoutFiles) {
    $semanticModelRoots += $lf.DirectoryName
  }
}

if ($semanticModelRoots.Count -eq 0) {
  Write-Host "No diagramLayout.json found under $rootResolved. Skipping diagram layout check." -ForegroundColor Yellow
  exit 0
}

$errors = @()
$warnings = @()

foreach ($smRoot in $semanticModelRoots) {
  $layoutFile = Join-Path $smRoot "diagramLayout.json"
  if (-not (Test-Path $layoutFile)) { continue }

  try {
    $json = Get-Content -Path $layoutFile -Raw | ConvertFrom-Json
    $relPath = $smRoot.Replace($repoRoot, "").TrimStart([System.IO.Path]::DirectorySeparatorChar)

    # Get nodes from first diagram
    if ($json.diagrams -and $json.diagrams.Count -gt 0 -and $json.diagrams[0].nodes) {
      $nodes = $json.diagrams[0].nodes
      $measuresNode = $nodes | Where-Object { $_.nodeIndex -eq "_Measures" } | Select-Object -First 1
      $factNodes = $nodes | Where-Object { $_.nodeIndex -like "fact_*" }
      $dimNodes = $nodes | Where-Object { ($_.nodeIndex -like "dim_*") -or ($_.nodeIndex -like "security_*") }

      # Check 1: _Measures at (0,0)
      if ($measuresNode) {
        $x = $measuresNode.location.x
        $y = $measuresNode.location.y
        if ($x -ne 0 -or $y -ne 0) {
          $errors += [PSCustomObject]@{ File = "$relPath/diagramLayout.json"; Rule = "diagram.measures_position"; Message = "_Measures must be at (0,0), found at ($x,$y)" }
        }
      } else {
        $warnings += [PSCustomObject]@{ File = "$relPath/diagramLayout.json"; Rule = "diagram.measures_missing"; Message = "_Measures table not found in diagram" }
      }

      # Check 2: Facts in horizontal row at y=0, starting x>=280
      $factXPositions = @($factNodes | ForEach-Object { $_.location.x } | Sort-Object)
      $factYPositions = @($factNodes | ForEach-Object { $_.location.y } | Sort-Object -Unique)
      if ($factNodes.Count -gt 0) {
        # All facts should be at y=0 (allow small tolerance)
        $nonZeroY = $factYPositions | Where-Object { $_ -ne 0 -and $_ -gt 5 }
        if ($nonZeroY.Count -gt 0) {
          $errors += [PSCustomObject]@{ File = "$relPath/diagramLayout.json"; Rule = "diagram.facts_y_position"; Message = "All fact tables must be at y=0, found at y=$($nonZeroY -join ',')" }
        }
        # First fact should be at x>=280
        if ($factXPositions.Count -gt 0 -and $factXPositions[0] -lt 250) {
          $errors += [PSCustomObject]@{ File = "$relPath/diagramLayout.json"; Rule = "diagram.facts_x_start"; Message = "First fact table should start at x>=280 (next to _Measures), found at x=$($factXPositions[0])" }
        }
        # Check spacing (should be ~250px, allow 200-300px tolerance)
        for ($i = 1; $i -lt $factXPositions.Count; $i++) {
          $spacing = $factXPositions[$i] - $factXPositions[$i - 1]
          if ($spacing -lt 200 -or $spacing -gt 300) {
            $warnings += [PSCustomObject]@{ File = "$relPath/diagramLayout.json"; Rule = "diagram.facts_spacing"; Message = "Fact table spacing should be ~250px, found $spacing px between $($factXPositions[$i-1]) and $($factXPositions[$i])" }
          }
        }
      }

      # Check 3: Dims in vertical column at x=0, starting y>=120
      $dimXPositions = @($dimNodes | ForEach-Object { $_.location.x } | Sort-Object -Unique)
      $dimYPositions = @($dimNodes | ForEach-Object { $_.location.y } | Sort-Object)
      if ($dimNodes.Count -gt 0) {
        # All dims should be at x=0 (allow small tolerance)
        $nonZeroX = $dimXPositions | Where-Object { $_ -ne 0 -and $_ -gt 5 }
        if ($nonZeroX.Count -gt 0) {
          $errors += [PSCustomObject]@{ File = "$relPath/diagramLayout.json"; Rule = "diagram.dims_x_position"; Message = "All dimension tables must be at x=0, found at x=$($nonZeroX -join ',')" }
        }
        # First dim should be at y>=120 (below _Measures)
        if ($dimYPositions.Count -gt 0 -and $dimYPositions[0] -lt 100) {
          $errors += [PSCustomObject]@{ File = "$relPath/diagramLayout.json"; Rule = "diagram.dims_y_start"; Message = "First dimension table should start at y>=120 (below _Measures), found at y=$($dimYPositions[0])" }
        }
        # Check spacing (should be ~120px, allow 100-150px tolerance)
        for ($i = 1; $i -lt $dimYPositions.Count; $i++) {
          $spacing = $dimYPositions[$i] - $dimYPositions[$i - 1]
          if ($spacing -lt 100 -or $spacing -gt 150) {
            $warnings += [PSCustomObject]@{ File = "$relPath/diagramLayout.json"; Rule = "diagram.dims_spacing"; Message = "Dimension table spacing should be ~120px, found $spacing px between y=$($dimYPositions[$i-1]) and y=$($dimYPositions[$i])" }
          }
        }
      }
    }
  } catch {
    $errors += [PSCustomObject]@{ File = "$relPath/diagramLayout.json"; Rule = "diagram.parse_error"; Message = "Failed to parse diagramLayout.json: $_" }
  }
}

if ($errors.Count -gt 0) {
  foreach ($e in $errors) {
    Write-Host "$($e.File) [ERROR] $($e.Rule) - $($e.Message)" -ForegroundColor Red
  }
}
if ($warnings.Count -gt 0) {
  foreach ($w in $warnings) {
    Write-Host "$($w.File) [WARN] $($w.Rule) - $($w.Message)" -ForegroundColor Yellow
  }
}

if ($errors.Count -gt 0) {
  Write-Host "Diagram layout check: $($errors.Count) error(s), $($warnings.Count) warning(s)." -ForegroundColor Red
  exit 1
}
if ($warnings.Count -gt 0) {
  Write-Host "Diagram layout check passed with $($warnings.Count) warning(s)." -ForegroundColor Yellow
  exit 0
}
Write-Host "Diagram layout check passed (spaghetti principle: _Measures top-left, facts horizontal, dims vertical)." -ForegroundColor Green
exit 0
