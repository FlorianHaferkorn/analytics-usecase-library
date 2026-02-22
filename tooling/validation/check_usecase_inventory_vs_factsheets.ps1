Param(
  [string]$UseCasesRoot = "core/usecases",
  [string]$InventoryPath = "core/usecases/UseCase_Inventory.md",
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

function Get-UseCaseIdsFromInventory {
  param([string]$Path)
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  if (-not (Test-Path $Path)) { return $ids }
  Get-Content -Path $Path | ForEach-Object {
    $line = $_
    foreach ($match in [regex]::Matches($line, '\b[A-Z]{2,3}-\d{3}\b')) {
      $null = $ids.Add($match.Value)
    }
  }
  return $ids
}

function Get-FactsheetIndex {
  param([string]$Root)
  $index = @{}
  Get-ChildItem -Path $Root -Recurse -Filter "*Factsheet*.md" | Where-Object {
    $_.FullName -notmatch '\\internal\\archive\\'
  } | ForEach-Object {
    if ($_.FullName -match '\\core\\usecases\\templates\\') { return }
    $content = Get-Content -Raw -Path $_.FullName
    $match = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---")
    if (-not $match.Success) { return }
    $frontMatter = $match.Groups[1].Value
    $idMatch = [regex]::Match($frontMatter, '^\s*id\s*:\s*"?([^"\s]+)"?', 'Multiline')
    $typeMatch = [regex]::Match($frontMatter, '^\s*factsheet_type\s*:\s*"?([^"\s]+)"?', 'Multiline')
    if (-not ($idMatch.Success -and $typeMatch.Success)) { return }
    $id = $idMatch.Groups[1].Value.Trim()
    $type = $typeMatch.Groups[1].Value.Trim().ToLowerInvariant()
    if (-not $index.ContainsKey($id)) { $index[$id] = @{} }
    $index[$id][$type] = $_.FullName
  }
  return $index
}

# Lean 2.0: Bracket is the machine-readable SSOT per use case (no Technical Factsheet).
function Test-UseCaseHasBracket {
  param([string]$UseCaseDirOrFactsheetPath)
  $dir = if (Test-Path -Path $UseCaseDirOrFactsheetPath -PathType Container) {
    $UseCaseDirOrFactsheetPath
  } else {
    Split-Path -Parent $UseCaseDirOrFactsheetPath
  }
  $bracketPath = Join-Path -Path $dir -ChildPath "UseCase_Bracket.yaml"
  return (Test-Path -Path $bracketPath -PathType Leaf)
}

$useCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative "core/usecases"
$inventoryPath = Resolve-RepoPath -ProvidedPath $InventoryPath -DefaultRelative "core/usecases/UseCase_Inventory.md"
if (-not $useCasesRoot) { throw "UseCases root not found. Provide -UseCasesRoot or run inside repository." }
if (-not $inventoryPath) { throw "UseCase inventory not found. Provide -InventoryPath or run inside repository." }

Write-Host "UseCase Inventory <-> Factsheets consistency" -ForegroundColor Cyan
$inventoryIds = Get-UseCaseIdsFromInventory -Path $inventoryPath
$factsheetIndex = Get-FactsheetIndex -Root $useCasesRoot
if (-not $factsheetIndex) { $factsheetIndex = @{} }

$missingBusiness = @()
$missingBracket = @()
foreach ($id in $inventoryIds) {
  if (-not $factsheetIndex.ContainsKey($id)) {
    $missingBusiness += $id
    continue
  }
  if (-not $factsheetIndex[$id].ContainsKey("business")) { $missingBusiness += $id; continue }
  $businessPath = $factsheetIndex[$id]["business"]
  if (-not (Test-UseCaseHasBracket -UseCaseDirOrFactsheetPath $businessPath)) {
    $missingBracket += $id
  }
}
$missingInventory = @()
foreach ($id in $factsheetIndex.Keys) {
  if (-not $inventoryIds.Contains($id)) { $missingInventory += $id }
}

if ($missingBusiness.Count -gt 0) {
  Write-Host "Missing Business Factsheets (listed in inventory):" -ForegroundColor Red
  $missingBusiness | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}
if ($missingBracket.Count -gt 0) {
  Write-Host "Missing UseCase_Bracket.yaml (listed in inventory, same folder as Business Factsheet):" -ForegroundColor Red
  $missingBracket | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}
if ($missingInventory.Count -gt 0) {
  Write-Host "Missing Inventory entries (factsheets exist):" -ForegroundColor Red
  $missingInventory | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}

if ($missingBusiness.Count -gt 0 -or $missingBracket.Count -gt 0 -or $missingInventory.Count -gt 0) {
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: inventory and factsheets are consistent." -ForegroundColor Green
