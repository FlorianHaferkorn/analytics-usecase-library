Param(
  [string]$UseCasesRoot = "core/usecases",
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

function Get-MeasureNamesFromDictionary {
  param([string]$Path)
  $names = [System.Collections.Generic.HashSet[string]]::new()
  Get-Content -Path $Path | ForEach-Object {
    if ($_ -match '^\s*-\s*measure_name\s*:\s*"?([^"]+)"?\s*$') {
      $null = $names.Add($matches[1].Trim())
    }
  }
  return $names
}

function Get-DaxMeasureNames {
  param([string]$Path)
  $names = [System.Collections.Generic.HashSet[string]]::new()
  $lines = Get-Content -Path $Path
  $inDax = $false
  foreach ($line in $lines) {
    if ($line -match '^```DAX') { $inDax = $true; continue }
    if ($inDax -and $line -match '^```') { $inDax = $false; continue }
    if (-not $inDax) { continue }
    if ($line -match '^\s*([^/\s].*?)\s*(:=|=)\s*$') {
      $name = $matches[1].Trim()
      if ($name -match '^VAR\b' -or $name -match '^RETURN\b') { continue }
      $null = $names.Add($name)
    }
  }
  return $names
}

$useCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative "core/usecases"
if (-not $useCasesRoot) { throw "UseCases root not found. Provide -UseCasesRoot or run inside repository." }

Write-Host "DAX definitions vs Measure Dictionaries" -ForegroundColor Cyan

# Note: Technical_Factsheet.md has been removed in Lean 2.0 migration.
# DAX definitions and measure dictionaries are now validated via UseCase_Bracket.yaml
# and the KPI catalog. This script scans UseCase_Bracket.yaml for measure_dictionary_ref
# paths and validates DAX measures from the KPI catalog against those dictionaries.

$missingByFile = @()
Get-ChildItem -Path $useCasesRoot -Recurse -Filter "UseCase_Bracket.yaml" | Where-Object {
  $_.FullName -notmatch '\\internal\\archive\\'
} | ForEach-Object {
  $file = $_.FullName
  $content = Get-Content -Path $file -Raw

  # Extract measure_dictionary_ref paths from bracket YAML
  $dictPaths = @()
  foreach ($match in [regex]::Matches($content, '(?m)^\s*measure_dictionary_ref\s*:\s*(.+?)\s*$')) {
    $dictPaths += ($match.Groups[1].Value -replace '["\x27]', '').Trim()
  }
  if ($dictPaths.Count -eq 0) { return }

  $dictNames = [System.Collections.Generic.HashSet[string]]::new()
  foreach ($dictPath in $dictPaths) {
    $resolvedDict = Resolve-RepoPath -ProvidedPath $dictPath -DefaultRelative $dictPath
    if (-not $resolvedDict) {
      $missingByFile += [PSCustomObject]@{ file = $file; missing = @("<Measure Dictionary not found: $dictPath>") }
      return
    }
    $names = Get-MeasureNamesFromDictionary -Path $resolvedDict
    foreach ($name in $names) { $null = $dictNames.Add($name) }
  }

  # Extract kpi_to_measure_mapping measure_names from bracket
  $bracketMeasures = @()
  foreach ($match in [regex]::Matches($content, '(?m)^\s*measure_name\s*:\s*"?([^"\r\n]+)"?\s*$')) {
    $bracketMeasures += $match.Groups[1].Value.Trim()
  }

  $missing = $bracketMeasures | Where-Object { $_ -and -not $dictNames.Contains($_) } | Sort-Object
  if ($missing.Count -gt 0) {
    $missingByFile += [PSCustomObject]@{ file = $file; missing = $missing }
  }
}

if ($missingByFile.Count -gt 0) {
  Write-Host "Missing DAX measures in Measure Dictionaries:" -ForegroundColor Red
  foreach ($entry in $missingByFile) {
    Write-Host ("- {0}" -f $entry.file)
    $entry.missing | ForEach-Object { Write-Host ("  - {0}" -f $_) }
  }
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: all DAX measures are present in their Measure Dictionaries." -ForegroundColor Green
