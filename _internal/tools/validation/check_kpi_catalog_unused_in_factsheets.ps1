Param(
  [string]$UseCasesRoot = "usecases",
  [string]$KpiCatalogRoot = "framework/kpi_catalog",
  [string]$InventoryPath = "usecases/UseCase_Inventory.md",
  [string]$ActionCodesRoot = "framework/action_codes",
  [string]$UseCaseActionCodeMapPath = "usecases/UseCase_ActionCode_Map.yaml",
  [string]$MeasureDictRoot = "semantic_models/domains",
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

function Get-FrontMatterText {
  param([string]$Path)
  $content = Get-Content -Raw -Path $Path
  $match = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---")
  if (-not $match.Success) { return $null }
  return $match.Groups[1].Value
}

function Get-BodyText {
  param([string]$Path)
  $content = Get-Content -Raw -Path $Path
  if (-not $content) { return "" }
  $withoutFrontMatter = [regex]::Replace($content, "(?ms)^---\s*\r?\n.*?\r?\n---\s*", "")
  return $withoutFrontMatter
}

function Parse-ListField {
  param([string]$FrontMatter,[string]$Field)
  if (-not $FrontMatter) { return @() }
  $escaped = [regex]::Escape($Field)
  $inline = [regex]::Match($FrontMatter, "^\s*$escaped\s*:\s*\[(.*?)\]", 'Multiline,Singleline')
  if ($inline.Success) {
    $items = @()
    foreach ($token in [regex]::Matches($inline.Groups[1].Value, '"([^"]+)"|''([^'']+)''|([^,\s\]]+)')) {
      $value = if ($token.Groups[1].Success) { $token.Groups[1].Value }
               elseif ($token.Groups[2].Success) { $token.Groups[2].Value }
               else { $token.Groups[3].Value }
      if ($value) { $items += $value }
    }
    return $items
  }
  $block = [regex]::Match($FrontMatter, "(?ms)^\s*$escaped\s*:\s*(?:#.*)?\r?\n(?<body>(?:\s{2,}-\s*[^\r\n]*\r?\n?)+)")
  if ($block.Success) {
    $results = @()
    foreach ($rawLine in ($block.Groups['body'].Value -split "\r?\n")) {
      $line = $rawLine.Trim()
      if (-not $line) { continue }
      if ($line -match '^\s*-\s*(.*)$') { $value = $matches[1].Trim() } else { continue }
      if (-not $value) { continue }
      if ($value -match '^(?<val>[^#]+)\s*(#.*)?$') { $value = $matches['val'].TrimEnd() }
      if ($value.StartsWith('"') -and $value.EndsWith('"')) {
        $value = $value.Trim('"')
      } elseif ($value.StartsWith("'") -and $value.EndsWith("'")) {
        $value = $value.Trim("'")
      }
      if ($value) { $results += $value }
    }
    return $results
  }
  return @()
}

function Get-MapKeys {
  param([string]$FrontMatter,[string]$Field)
  $escaped = [regex]::Escape($Field)
  $match = [regex]::Match($FrontMatter, "^\s*$escaped\s*:\s*$", 'Multiline')
  if (-not $match.Success) { return @() }
  $keys = @()
  $startIndex = $match.Index + $match.Length
  $lines = $FrontMatter.Substring($startIndex) -split "\r?\n"
  foreach ($line in $lines) {
    if ($line.Trim().Length -eq 0) { continue }
    if ($line -notmatch "^\s+") { break }
    $kv = [regex]::Match($line, "^\s*([^:]+):\s*[`"'](.*?)[`"']\s*$")
    if ($kv.Success) { $keys += $kv.Groups[1].Value.Trim() }
  }
  return $keys
}

function Get-KpiTokensFromText {
  param([string]$Text)
  if (-not $Text) { return @() }
  $tokens = [System.Collections.Generic.HashSet[string]]::new()
  foreach ($match in [regex]::Matches($Text, '\b[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+\b')) {
    $null = $tokens.Add($match.Value)
  }
  return $tokens
}

function Get-KpiIdsFromCatalog {
  param([string]$Root)
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  $catalogPath = Join-Path -Path $Root -ChildPath "KPI_Catalog.md"
  if (Test-Path $catalogPath) {
    Get-Content -Path $catalogPath | ForEach-Object {
      if ($_ -match '^\s*-\s*kpi_id\s*:\s*"?([^"\s]+)"?') {
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
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  Get-ChildItem -Path $coreRoot -Recurse -Filter "*Factsheet*.md" | Where-Object {
    $_.FullName -notmatch '\\_internal\\archive\\'
  } | ForEach-Object {
    $fm = Get-FrontMatterText -Path $_.FullName
    if (-not $fm) { return }
    $match = [regex]::Match($fm, "^\s*id\s*:\s*([A-Z0-9-]+)\s*$", "Multiline")
    if ($match.Success) { $null = $ids.Add($match.Groups[1].Value.Trim()) }
  }
  return $ids
}

function Get-ActionCodesForUseCases {
  param([string]$MapPath,[System.Collections.Generic.HashSet[string]]$UseCaseIds)
  if (-not (Test-Path $MapPath)) { return @() }
  $codes = [System.Collections.Generic.HashSet[string]]::new()
  $currentId = $null
  foreach ($line in Get-Content -Path $MapPath) {
    $useCaseMatch = [regex]::Match($line, '^\s{2}([A-Z0-9-]+):\s*$')
    if ($useCaseMatch.Success) {
      $currentId = $useCaseMatch.Groups[1].Value.Trim()
      continue
    }
    if (-not $currentId) { continue }
    if (-not $UseCaseIds.Contains($currentId)) { continue }
    $codesMatch = [regex]::Match($line, '^\s{4}action_codes:\s*\[(.*?)\]\s*$')
    if ($codesMatch.Success) {
      foreach ($token in ($codesMatch.Groups[1].Value -split ',')) {
        $value = $token.Trim().Trim('"').Trim("'")
        if ($value) { $null = $codes.Add($value) }
      }
    }
  }
  return $codes
}

function Get-ActionCodesFromFactsheets {
  param([string]$Root)
  $coreRoot = Join-Path -Path $Root -ChildPath "core"
  if (-not (Test-Path $coreRoot)) { return @() }
  $codes = [System.Collections.Generic.HashSet[string]]::new()
  Get-ChildItem -Path $coreRoot -Recurse -Filter "*Factsheet*.md" | Where-Object {
    $_.FullName -notmatch '\\_internal\\archive\\'
  } | ForEach-Object {
    $body = Get-BodyText -Path $_.FullName
    if (-not $body) { return }
    foreach ($match in [regex]::Matches($body, '\b[A-Z]{1,3}-[A-Z][0-9]\.[0-9]\b')) {
      $null = $codes.Add($match.Value)
    }
  }
  return $codes
}

function Get-KpiIdsFromActionCodes {
  param([string]$Root,[System.Collections.Generic.HashSet[string]]$ActionCodes,[System.Collections.Generic.HashSet[string]]$CatalogIds)
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  if (-not $ActionCodes -or $ActionCodes.Count -eq 0) { return $ids }
  foreach ($code in $ActionCodes) {
    $matches = Get-ChildItem -Path $Root -Recurse -Filter "$code.yaml" -File -ErrorAction SilentlyContinue | Where-Object {
      $_.FullName -notmatch '\\_internal\\archive\\'
    }
    if (-not $matches) { continue }
    $path = $matches[0].FullName
    foreach ($line in Get-Content -Path $path) {
      if ($line -match '^\s*kpi_id\s*:\s*"?([^"\s]+)"?') {
        $value = $matches[1]
        if ($CatalogIds.Contains($value)) { $null = $ids.Add($value) }
        continue
      }
      if ($line -match '^\s*metric_kpi_id\s*:\s*"?([^"\s]+)"?') {
        $value = $matches[1]
        if ($CatalogIds.Contains($value)) { $null = $ids.Add($value) }
      }
    }
  }
  return $ids
}

function Get-KpiIdsFromMeasureDictionaries {
  param([string]$Root,[System.Collections.Generic.HashSet[string]]$CatalogIds)
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  if (-not (Test-Path $Root)) { return $ids }
  Get-ChildItem -Path $Root -Recurse -Filter "Measure_Dictionary_*.md" -File | Where-Object {
    $_.FullName -notmatch '\\_internal\\archive\\'
  } | ForEach-Object {
    foreach ($line in Get-Content -Path $_.FullName) {
      if ($line -match '^\s*kpi_id_ref\s*:\s*"?([^"\s]+)"?') {
        $value = $matches[1]
        if ($value -and $CatalogIds.Contains($value)) { $null = $ids.Add($value) }
      }
    }
  }
  return $ids
}

$useCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative "usecases"
$kpiCatalogRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative "framework/kpi_catalog"
$inventoryPath = Resolve-RepoPath -ProvidedPath $InventoryPath -DefaultRelative "usecases/UseCase_Inventory.md"
$actionCodesRoot = Resolve-RepoPath -ProvidedPath $ActionCodesRoot -DefaultRelative "framework/action_codes"
$actionCodeMapPath = Resolve-RepoPath -ProvidedPath $UseCaseActionCodeMapPath -DefaultRelative "usecases/UseCase_ActionCode_Map.yaml"
$measureDictRoot = Resolve-RepoPath -ProvidedPath $MeasureDictRoot -DefaultRelative "semantic_models/domains"
if (-not $useCasesRoot) { throw "UseCases root not found. Provide -UseCasesRoot or run inside repository." }
if (-not $kpiCatalogRoot) { throw "KPI catalog root not found. Provide -KpiCatalogRoot or run inside repository." }

Write-Host "KPI Catalog -> Factsheets coverage" -ForegroundColor Cyan
Write-Host "Note: This list checks core factsheets, core action codes, inventory mentions, and measure dictionaries." -ForegroundColor DarkGray
Write-Host "It does not consider KPI aliases or KPIs used only as intermediate inputs." -ForegroundColor DarkGray
$catalogIds = Get-KpiIdsFromCatalog -Root $kpiCatalogRoot
$inventoryRefs = [System.Collections.Generic.HashSet[string]]::new()
$factsheetRefs = [System.Collections.Generic.HashSet[string]]::new()
$actionCodeRefs = [System.Collections.Generic.HashSet[string]]::new()
$measureDictRefs = [System.Collections.Generic.HashSet[string]]::new()
$allRefs = [System.Collections.Generic.HashSet[string]]::new()
foreach ($id in (Get-KpiTokensFromText -Text (Get-Content -Raw -Path $inventoryPath -ErrorAction SilentlyContinue))) {
  if ($catalogIds.Contains($id)) { $null = $inventoryRefs.Add($id) }
}

Get-ChildItem -Path $useCasesRoot -Recurse -Filter "*Factsheet*.md" | Where-Object {
  $_.FullName -notmatch '\\_internal\\archive\\'
} | ForEach-Object {
  $fm = Get-FrontMatterText -Path $_.FullName
  if (-not $fm) { return }
  foreach ($id in (Parse-ListField -FrontMatter $fm -Field "required_kpi_ids")) { $null = $factsheetRefs.Add($id) }
  foreach ($id in (Parse-ListField -FrontMatter $fm -Field "supports_strategic_kpi_ids")) { $null = $factsheetRefs.Add($id) }
  foreach ($id in (Get-MapKeys -FrontMatter $fm -Field "required_kpis")) { $null = $factsheetRefs.Add($id) }
  foreach ($id in (Get-KpiTokensFromText -Text (Get-BodyText -Path $_.FullName))) {
    if ($catalogIds.Contains($id)) { $null = $factsheetRefs.Add($id) }
  }
}

$coreUseCaseIds = Get-CoreUseCaseIds -Root $useCasesRoot
$actionCodes = [System.Collections.Generic.HashSet[string]]::new()
if ($coreUseCaseIds.Count -gt 0 -and $actionCodesRoot -and $actionCodeMapPath) {
  foreach ($code in (Get-ActionCodesForUseCases -MapPath $actionCodeMapPath -UseCaseIds $coreUseCaseIds)) {
    $null = $actionCodes.Add($code)
  }
}
foreach ($code in (Get-ActionCodesFromFactsheets -Root $useCasesRoot)) {
  $null = $actionCodes.Add($code)
}
if ($actionCodesRoot) {
  foreach ($id in (Get-KpiIdsFromActionCodes -Root $actionCodesRoot -ActionCodes $actionCodes -CatalogIds $catalogIds)) {
    $null = $actionCodeRefs.Add($id)
  }
}

if ($measureDictRoot) {
  foreach ($id in (Get-KpiIdsFromMeasureDictionaries -Root $measureDictRoot -CatalogIds $catalogIds)) {
    $null = $measureDictRefs.Add($id)
  }
}

foreach ($id in $inventoryRefs) { $null = $allRefs.Add($id) }
foreach ($id in $factsheetRefs) { $null = $allRefs.Add($id) }
foreach ($id in $actionCodeRefs) { $null = $allRefs.Add($id) }
foreach ($id in $measureDictRefs) { $null = $allRefs.Add($id) }

Write-Host "Coverage counts (unique KPI IDs):" -ForegroundColor DarkGray
Write-Host ("  Factsheets:           {0}" -f $factsheetRefs.Count) -ForegroundColor DarkGray
Write-Host ("  Inventory:            {0}" -f $inventoryRefs.Count) -ForegroundColor DarkGray
Write-Host ("  Core Action Codes:    {0}" -f $actionCodeRefs.Count) -ForegroundColor DarkGray
Write-Host ("  Measure Dictionaries: {0}" -f $measureDictRefs.Count) -ForegroundColor DarkGray
Write-Host ("  Total covered:        {0}" -f $allRefs.Count) -ForegroundColor DarkGray

$unused = $catalogIds | Where-Object { -not $allRefs.Contains($_) } | Sort-Object

if ($unused.Count -gt 0) {
  Write-Host "KPI IDs not referenced in factsheets:" -ForegroundColor Yellow
  $unused | ForEach-Object { Write-Host "  - $_" }
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: all KPI IDs are referenced in factsheets." -ForegroundColor Green

