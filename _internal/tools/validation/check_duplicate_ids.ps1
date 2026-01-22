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

$issues = @()

# Action Code IDs
$actionCodeIds = @{}
Get-ChildItem -Path (Join-Path $rootPath "framework\action_codes") -Recurse -Filter "*.yaml" | Where-Object {
  $_.FullName -notmatch '\\decision_spines\\' -and $_.FullName -notmatch '\\_internal\\archive\\'
} | ForEach-Object {
  $id = $null
  Get-Content -Path $_.FullName | ForEach-Object {
    if (-not $id -and $_ -match '^\s*id\s*:\s*"?([^"\s]+)"?') { $id = $matches[1] }
  }
  if (-not $id) {
    $issues += "$($_.FullName): missing action code id"
    return
  }
  if ($actionCodeIds.ContainsKey($id)) { $issues += "Duplicate Action Code id '$id' in $($_.FullName) and $($actionCodeIds[$id])" }
  else { $actionCodeIds[$id] = $_.FullName }
}

# Use Case IDs (inventory)
$inventoryPath = Join-Path $rootPath "usecases\UseCase_Inventory.md"
if (Test-Path $inventoryPath) {
  $invCounts = @{}
  Get-Content -Path $inventoryPath | ForEach-Object {
    foreach ($m in [regex]::Matches($_, '\b[A-Z]{2,3}-\d{3}\b')) {
      $id = $m.Value
      if (-not $invCounts.ContainsKey($id)) { $invCounts[$id] = 0 }
      $invCounts[$id]++
    }
  }
  foreach ($kv in $invCounts.GetEnumerator()) {
    if ($kv.Value -gt 1) { $issues += "Duplicate Use Case id '$($kv.Key)' in inventory" }
  }
}

# Factsheet IDs (by type)
Get-ChildItem -Path (Join-Path $rootPath "usecases") -Recurse -Filter "*Factsheet*.md" | Where-Object {
  $_.FullName -notmatch '\\_internal\\archive\\' -and $_.FullName -notmatch '\\usecases\\templates\\'
} | ForEach-Object {
  $content = Get-Content -Raw -Path $_.FullName
  $match = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---")
  if (-not $match.Success) { return }
  $fm = $match.Groups[1].Value
  $idMatch = [regex]::Match($fm, '^\s*id\s*:\s*"?([^"\s]+)"?', 'Multiline')
  $typeMatch = [regex]::Match($fm, '^\s*factsheet_type\s*:\s*"?([^"\s]+)"?', 'Multiline')
  if (-not ($idMatch.Success -and $typeMatch.Success)) { return }
  $id = $idMatch.Groups[1].Value.Trim()
  $type = $typeMatch.Groups[1].Value.Trim().ToLowerInvariant()
  $key = "$id|$type"
  if (-not $script:factsheetIds) { $script:factsheetIds = @{} }
  if ($script:factsheetIds.ContainsKey($key)) { $issues += "Duplicate factsheet id '$id' for type '$type' in $($_.FullName) and $($script:factsheetIds[$key])" }
  else { $script:factsheetIds[$key] = $_.FullName }
}

# Decision Spine IDs
$spineIds = @{}
Get-ChildItem -Path (Join-Path $rootPath "framework\action_codes\decision_spines") -Filter "*.yaml" | Where-Object {
  $_.Name -ne "DecisionSpine_UseCase_Map.yaml"
} | ForEach-Object {
  $id = $null
  Get-Content -Path $_.FullName | ForEach-Object {
    if (-not $id -and $_ -match '^\s*id\s*:\s*"?([^"\s]+)"?') { $id = $matches[1] }
  }
  if (-not $id) {
    $issues += "$($_.FullName): missing decision spine id"
    return
  }
  if ($spineIds.ContainsKey($id)) { $issues += "Duplicate Decision Spine id '$id' in $($_.FullName) and $($spineIds[$id])" }
  else { $spineIds[$id] = $_.FullName }
}

# Data contract table names (per file)
Get-ChildItem -Path (Join-Path $rootPath "data_contracts\domains") -Recurse -Filter "*.yaml" | Where-Object {
  $_.FullName -notmatch '\\_internal\\archive\\'
} | ForEach-Object {
  $seen = @{}
  Get-Content -Path $_.FullName | ForEach-Object {
    if ($_ -match '^\s*-\s*name\s*:\s*([A-Za-z0-9_]+)\s*$') {
      $name = $matches[1]
      if ($seen.ContainsKey($name)) { $issues += "Duplicate table name '$name' in $($_.FullName)" }
      else { $seen[$name] = $true }
    }
  }
}

if ($issues.Count -gt 0) {
  Write-Host "Duplicate ID checks failed:" -ForegroundColor Red
  $issues | Sort-Object | ForEach-Object { Write-Host "  - $_" }
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: no duplicate IDs detected." -ForegroundColor Green
