Param(
  [string]$UseCasesRoot = "core/usecases",
  [string]$MapPath = "core/usecases/UseCase_ActionCode_Map.yaml",
  [string]$ActionCodesRoot = "core/action_codes",
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

function Get-MapEntries {
  param([string]$Path)
  $lines = Get-Content -Path $Path
  $map = @{}
  $current = $null
  foreach ($line in $lines) {
    if ($line -match '^\s{2}([A-Z]{2,3}-\d{3}):\s*$') {
      $current = $matches[1]
      continue
    }
    if ($current -and $line -match '^\s{4}action_codes:\s*\[(.*?)\]\s*$') {
      $codes = $matches[1].Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ }
      $map[$current] = $codes
      $current = $null
    }
  }
  return $map
}

function Get-ActionCodeIds {
  param([string]$Root)
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  Get-ChildItem -Path $Root -Recurse -File | Where-Object {
    $_.Extension -in @(".yaml",".yml") -and $_.FullName -notmatch '\\_internal\\archive\\'
  } | ForEach-Object {
    $basename = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
    if ($basename) { $null = $ids.Add($basename) }
    Get-Content -Path $_.FullName | ForEach-Object {
      if ($_ -match '^\s*id\s*:\s*"?([^"\s]+)"?') {
        $null = $ids.Add($matches[1])
      }
    }
  }
  return $ids
}

function Get-CoreUseCaseIds {
  param([string]$Root)
  $coreRoot = Join-Path -Path $Root -ChildPath "core"
  if (-not (Test-Path $coreRoot)) { return @() }
  return Get-ChildItem -Path $coreRoot -Directory | ForEach-Object { $_.Name.Split('_')[0] } | Sort-Object -Unique
}

$useCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative "core/usecases"
$mapPath = Resolve-RepoPath -ProvidedPath $MapPath -DefaultRelative "core/usecases/UseCase_ActionCode_Map.yaml"
$actionCodesRoot = Resolve-RepoPath -ProvidedPath $ActionCodesRoot -DefaultRelative "core/action_codes"

if (-not $useCasesRoot) { throw "UseCases root not found. Provide -UseCasesRoot or run inside repository." }
if (-not $mapPath) { throw "UseCase ActionCode map not found. Provide -MapPath or run inside repository." }
if (-not $actionCodesRoot) { throw "Action codes root not found. Provide -ActionCodesRoot or run inside repository." }

Write-Host "UseCase ActionCode map consistency" -ForegroundColor Cyan

$mapEntries = Get-MapEntries -Path $mapPath
$mapUseCases = $mapEntries.Keys | Sort-Object
$coreUseCases = Get-CoreUseCaseIds -Root $useCasesRoot
$actionCodeIds = Get-ActionCodeIds -Root $actionCodesRoot

$missingCore = $coreUseCases | Where-Object { $_ -notin $mapUseCases }
$nonCore = $mapUseCases | Where-Object { $_ -notin $coreUseCases }

$missingCodes = @()
foreach ($entry in $mapEntries.GetEnumerator()) {
  foreach ($code in $entry.Value) {
    if (-not $actionCodeIds.Contains($code)) {
      $missingCodes += "$($entry.Key): $code"
    }
  }
}

$hadIssues = $false
if ($missingCore.Count -gt 0) {
  $hadIssues = $true
  Write-Host "Missing core use cases in map:" -ForegroundColor Red
  $missingCore | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}
if ($nonCore.Count -gt 0) {
  $hadIssues = $true
  Write-Host "Non-core use cases still present in map:" -ForegroundColor Red
  $nonCore | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}
if ($missingCodes.Count -gt 0) {
  $hadIssues = $true
  Write-Host "Missing Action Codes (referenced in map):" -ForegroundColor Red
  $missingCodes | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}

if ($hadIssues) {
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: UseCase ActionCode map is consistent with core and action codes." -ForegroundColor Green
