param(
  [string]$MeasureDictRoot = (Join-Path $PSScriptRoot "..\..\..\semantic_models\domains"),
  [string]$DistRoot = (Join-Path $PSScriptRoot "..\..\..\dist")
)

$ErrorActionPreference = "Stop"

$tmdlFiles = Get-ChildItem -Path $DistRoot -Recurse -Filter "*_Measures.tmdl" -ErrorAction SilentlyContinue
if (-not $tmdlFiles -or $tmdlFiles.Count -eq 0) {
  Write-Host "No _Measures.tmdl files found under dist. Skipping TMDL check."
  exit 0
}

function Get-MeasureNamesFromDict {
  param([string]$Root)
  $names = New-Object System.Collections.Generic.HashSet[string]
  Get-ChildItem -Path $Root -Recurse -Filter "Measure_Dictionary_*.md" | ForEach-Object {
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

if ($missingInTmdl.Count -eq 0 -and $missingInDict.Count -eq 0) {
  Write-Host "OK: TMDL measures align with Measure Dictionaries."
  exit 0
}

if ($missingInTmdl.Count -gt 0) {
  Write-Host "Missing in TMDL (present in Measure Dictionaries):"
  $missingInTmdl | ForEach-Object { Write-Host "  - $_" }
}

if ($missingInDict.Count -gt 0) {
  Write-Host "Missing in Measure Dictionaries (present in TMDL):"
  $missingInDict | ForEach-Object { Write-Host "  - $_" }
}

exit 1
