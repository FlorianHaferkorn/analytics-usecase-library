param(
  [string]$MeasureDictRoot,
  [string]$DistRoot
)

$ErrorActionPreference = "Stop"

# Resolve repo root from script location: products/fabric_powerbi/tooling/validation -> ../../..
$scriptDir = $PSScriptRoot
$repoRoot = (Get-Item $scriptDir).Parent.Parent.Parent.FullName
if (-not $MeasureDictRoot) { $MeasureDictRoot = Join-Path $repoRoot "core\semantic_models\domains" }
if (-not $DistRoot) { $DistRoot = Join-Path $repoRoot "products\fabric_powerbi\dist" }

$tmdlFiles = Get-ChildItem -Path $DistRoot -Recurse -Filter "*_Measures.tmdl" -ErrorAction SilentlyContinue | Where-Object {
  $_.FullName -notmatch '\\internal\\archive\\'
}
if (-not $tmdlFiles -or $tmdlFiles.Count -eq 0) {
  Write-Host "No _Measures.tmdl files found under DistRoot. Skipping TMDL check."
  exit 0
}

function Get-MeasureNamesFromDict {
  param([string]$Root)
  $names = New-Object System.Collections.Generic.HashSet[string]
  Get-ChildItem -Path $Root -Recurse -Filter "Measure_Dictionary_*.md" | Where-Object {
    $_.FullName -notmatch '\\internal\\archive\\'
  } | ForEach-Object {
    Get-Content $_.FullName | ForEach-Object {
      if ($_ -match '^\s*-?\s*measure_name:\s*"?(.+?)"?\s*$') {
        $name = $Matches[1].Trim()
        if ($name) { $names.Add($name) | Out-Null }
      }
    }
  }
  return $names
}

function Get-MeasureNamesFromTmdl {
  param($Files)
  $names = New-Object System.Collections.Generic.HashSet[string]
  $regex = [regex]::new('(?im)^\s*measure\s+[''"]?([^''"\r\n]+)[''"]?\s*=')
  foreach ($file in $Files) {
    $text = Get-Content $file.FullName -Raw
    foreach ($m in $regex.Matches($text)) {
      $name = $m.Groups[1].Value.Trim()
      if ($name) { $names.Add($name) | Out-Null }
    }
  }
  return $names
}

$dictMeasures = Get-MeasureNamesFromDict -Root $MeasureDictRoot
$tmdlMeasures = Get-MeasureNamesFromTmdl -Files $tmdlFiles

$missingInTmdl = $dictMeasures | Where-Object { $_ -notin $tmdlMeasures } | Sort-Object
$missingInDict = $tmdlMeasures | Where-Object { $_ -notin $dictMeasures } | Sort-Object

Write-Host "TMDL <-> Measure Dictionary consistency"

# Fail only when a TMDL measure has no dictionary entry (governance: every emitted measure must be documented).
# "Missing in TMDL" is informational: dictionary measures not yet implemented in dist are expected.
if ($missingInDict.Count -gt 0) {
  Write-Host "Missing in Measure Dictionaries (present in TMDL):" -ForegroundColor Red
  $missingInDict | ForEach-Object { Write-Host "  - $_" }
  exit 1
}

if ($missingInTmdl.Count -gt 0) {
  Write-Host "Info: Dictionary measures not yet in any TMDL (expected when dist is a subset): $($missingInTmdl.Count) measures."
}

Write-Host "OK: Every TMDL measure has a Measure Dictionary entry."
exit 0
