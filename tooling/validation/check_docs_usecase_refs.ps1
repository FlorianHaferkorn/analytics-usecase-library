Param(
  [string]$DocsRoot = "framework/strategy_operating_model",
  [string]$UseCasesRoot = "framework/usecases",
  [string]$InventoryPath = "framework/usecases/UseCase_Inventory.md",
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
    foreach ($match in [regex]::Matches($_, '\b[A-Z]{3}-\d{3}\b')) {
      $null = $ids.Add($match.Value)
    }
  }
  return $ids
}

function Get-UseCaseIdsFromFactsheets {
  param([string]$Root)
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  Get-ChildItem -Path $Root -Recurse -Filter "*Factsheet*.md" | Where-Object {
    $_.FullName -notmatch '\\_internal\\archive\\'
  } | ForEach-Object {
    $content = Get-Content -Raw -Path $_.FullName
    $match = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---")
    if (-not $match.Success) { return }
    $frontMatter = $match.Groups[1].Value
    $idMatch = [regex]::Match($frontMatter, '^\s*id\s*:\s*"?([^"\s]+)"?', 'Multiline')
    if ($idMatch.Success) { $null = $ids.Add($idMatch.Groups[1].Value.Trim()) }
  }
  return $ids
}

function Get-UseCaseIdsFromDocs {
  param([string]$Root)
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  Get-ChildItem -Path $Root -Recurse -File | Where-Object {
    $_.Extension -in @(".md",".yaml",".yml") -and $_.FullName -notmatch '\\_internal\\archive\\'
  } | ForEach-Object {
    Get-Content -Path $_.FullName | ForEach-Object {
      foreach ($match in [regex]::Matches($_, '\b[A-Z]{3}-\d{3}\b')) {
        $null = $ids.Add($match.Value)
      }
    }
  }
  return $ids
}

$docsRoot = Resolve-RepoPath -ProvidedPath $DocsRoot -DefaultRelative "framework/strategy_operating_model"
$useCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative "framework/usecases"
$inventoryPath = Resolve-RepoPath -ProvidedPath $InventoryPath -DefaultRelative "framework/usecases/UseCase_Inventory.md"
if (-not $docsRoot) { throw "Docs root not found. Provide -DocsRoot or run inside repository." }
if (-not $useCasesRoot) { throw "UseCases root not found. Provide -UseCasesRoot or run inside repository." }
if (-not $inventoryPath) { throw "UseCase inventory not found. Provide -InventoryPath or run inside repository." }

Write-Host "Docs -> UseCase references consistency" -ForegroundColor Cyan
$docIds = Get-UseCaseIdsFromDocs -Root $docsRoot
$inventoryIds = Get-UseCaseIdsFromInventory -Path $inventoryPath
$factsheetIds = Get-UseCaseIdsFromFactsheets -Root $useCasesRoot
if (-not $factsheetIds) { $factsheetIds = [System.Collections.Generic.HashSet[string]]::new() }

$missingInventory = $docIds | Where-Object { -not $inventoryIds.Contains($_) } | Sort-Object
$missingFactsheets = $docIds | Where-Object { -not $factsheetIds.Contains($_) } | Sort-Object

if ($missingInventory.Count -gt 0) {
  Write-Host "UseCase IDs referenced in docs but missing in inventory:" -ForegroundColor Red
  $missingInventory | ForEach-Object { Write-Host "  - $_" }
}
if ($missingFactsheets.Count -gt 0) {
  Write-Host "UseCase IDs referenced in docs but missing factsheets:" -ForegroundColor Red
  $missingFactsheets | ForEach-Object { Write-Host "  - $_" }
}

if ($missingInventory.Count -gt 0 -or $missingFactsheets.Count -gt 0) {
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: docs use case references are consistent." -ForegroundColor Green
