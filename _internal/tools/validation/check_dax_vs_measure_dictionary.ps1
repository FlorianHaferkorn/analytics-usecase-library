Param(
  [string]$UseCasesRoot = "usecases",
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

$useCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative "usecases"
if (-not $useCasesRoot) { throw "UseCases root not found. Provide -UseCasesRoot or run inside repository." }

Write-Host "DAX definitions vs Measure Dictionaries" -ForegroundColor Cyan

$missingByFile = @()
Get-ChildItem -Path $useCasesRoot -Recurse -Filter "Technical_Factsheet.md" | Where-Object {
  $_.FullName -notmatch '\\_internal\\archive\\'
} | ForEach-Object {
  $file = $_.FullName
  $daxNames = Get-DaxMeasureNames -Path $file
  if ($daxNames.Count -eq 0) { return }

  $dictPaths = @()
  Get-Content -Path $file | ForEach-Object {
    if ($_ -match '^\s*-\s*\*\*Measure Dictionary:\*\*\s*(.+?)\s*$') {
      $dictPaths += ($matches[1] -split ',') | ForEach-Object { $_.Trim() } | Where-Object { $_ }
    }
  }
  if ($dictPaths.Count -eq 0) {
    $missingByFile += [PSCustomObject]@{ file = $file; missing = @("<Measure Dictionary path not found>") }
    return
  }

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

  $missing = $daxNames | Where-Object { -not $dictNames.Contains($_) } | Sort-Object
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
