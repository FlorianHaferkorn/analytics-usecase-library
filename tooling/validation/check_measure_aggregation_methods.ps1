Param(
  [string]$Root = ".",
  [switch]$FailOnError
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

# Valid aggregation methods per framework convention
$validMethods = @("sum", "average", "last_value", "ratio", "count", "min", "max")

$issues = @()
$warnings = @()
$checkedMeasures = 0
$missingCount = 0

$measureDictDir = Join-Path $rootPath "core\semantic_models\domains"
$dictFiles = Get-ChildItem -Path $measureDictDir -Recurse -Filter "Measure_Dictionary_*.md" -ErrorAction SilentlyContinue

if (-not $dictFiles) {
  Write-Host "WARN: No Measure Dictionary files found in $measureDictDir" -ForegroundColor Yellow
  exit 0
}

foreach ($file in $dictFiles) {
  $lines = Get-Content -Path $file.FullName
  $inMeasureBlock = $false
  $currentMeasureId = $null
  $foundAggMethod = $false
  $lineNum = 0

  foreach ($line in $lines) {
    $lineNum++

    # Detect measure ID line (e.g., "  id: kpi.gross_margin_pct")
    if ($line -match '^\s{2,4}id\s*:\s*([a-z][\w\.]+)\s*$') {
      # Save previous measure if applicable
      if ($currentMeasureId -and -not $foundAggMethod) {
        $missingCount++
        $issues += "$($file.Name) line (before $lineNum): measure '$currentMeasureId' missing aggregation_method"
      }
      $currentMeasureId = $matches[1]
      $foundAggMethod = $false
      $checkedMeasures++
      $inMeasureBlock = $true
    }

    # Detect aggregation_method field
    if ($inMeasureBlock -and $line -match '^\s+aggregation_method\s*:\s*(.+)\s*$') {
      $method = $matches[1].Trim().Trim('"').ToLowerInvariant()
      if ($method -notin $validMethods) {
        $issues += "$($file.Name): measure '$currentMeasureId' has invalid aggregation_method '$method' (valid: $($validMethods -join ', '))"
      }
      $foundAggMethod = $true
    }

    # Detect end of YAML block (new top-level measure or section)
    if ($line -match '^- id\s*:' -or $line -match '^  - id\s*:') {
      if ($currentMeasureId -and -not $foundAggMethod) {
        $missingCount++
        $issues += "$($file.Name): measure '$currentMeasureId' missing aggregation_method"
      }
      $currentMeasureId = $null
      $foundAggMethod = $false
      $inMeasureBlock = $false
    }
  }

  # Check last measure in file
  if ($currentMeasureId -and -not $foundAggMethod) {
    $missingCount++
    $issues += "$($file.Name): measure '$currentMeasureId' missing aggregation_method"
  }
}

Write-Host "Checked $checkedMeasures measure entries across $($dictFiles.Count) Measure Dictionary files."

if ($issues.Count -gt 0) {
  Write-Host "Aggregation method check: $missingCount measures missing aggregation_method:" -ForegroundColor Yellow
  $issues | ForEach-Object { Write-Host "  - $_" }
  if ($FailOnError) { exit 1 }
  Write-Host "WARN: aggregation_method gaps found (non-failing in current mode)." -ForegroundColor Yellow
  exit 0
}

Write-Host "OK: all checked measures have aggregation_method defined." -ForegroundColor Green
