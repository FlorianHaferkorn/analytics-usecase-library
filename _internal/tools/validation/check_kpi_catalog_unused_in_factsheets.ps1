Param(
  [string]$UseCasesRoot = "usecases",
  [string]$KpiCatalogRoot = "framework/kpi_catalog",
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

function Get-KpiIdsFromCatalog {
  param([string]$Root)
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  Get-ChildItem -Path $Root -Recurse -Filter "KPI_Catalog_*.md" | ForEach-Object {
    Get-Content -Path $_.FullName | ForEach-Object {
      if ($_ -match '^\s*-\s*kpi_id\s*:\s*"?([^"\s]+)"?') {
        $null = $ids.Add($matches[1])
      }
    }
  }
  return $ids
}

$useCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative "usecases"
$kpiCatalogRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative "framework/kpi_catalog"
if (-not $useCasesRoot) { throw "UseCases root not found. Provide -UseCasesRoot or run inside repository." }
if (-not $kpiCatalogRoot) { throw "KPI catalog root not found. Provide -KpiCatalogRoot or run inside repository." }

Write-Host "KPI Catalog -> Factsheets coverage" -ForegroundColor Cyan
Write-Host "Note: This list only checks direct mentions in factsheets. It does not consider:" -ForegroundColor DarkGray
Write-Host "  a) KPIs used as inputs to measures referenced by factsheets," -ForegroundColor DarkGray
Write-Host "  b) KPIs missing in factsheets but still relevant," -ForegroundColor DarkGray
Write-Host "  c) KPIs required by Action Codes for core factsheets," -ForegroundColor DarkGray
Write-Host "  d) KPIs that exist under different names/aliases." -ForegroundColor DarkGray
$catalogIds = Get-KpiIdsFromCatalog -Root $kpiCatalogRoot
$factsheetRefs = [System.Collections.Generic.HashSet[string]]::new()

Get-ChildItem -Path $useCasesRoot -Recurse -Filter "*Factsheet*.md" | ForEach-Object {
  $fm = Get-FrontMatterText -Path $_.FullName
  if (-not $fm) { return }
  foreach ($id in (Parse-ListField -FrontMatter $fm -Field "required_kpi_ids")) { $null = $factsheetRefs.Add($id) }
  foreach ($id in (Parse-ListField -FrontMatter $fm -Field "supports_strategic_kpi_ids")) { $null = $factsheetRefs.Add($id) }
  foreach ($id in (Get-MapKeys -FrontMatter $fm -Field "required_kpis")) { $null = $factsheetRefs.Add($id) }
}

$unused = $catalogIds | Where-Object { -not $factsheetRefs.Contains($_) } | Sort-Object

if ($unused.Count -gt 0) {
  Write-Host "KPI IDs not referenced in factsheets:" -ForegroundColor Yellow
  $unused | ForEach-Object { Write-Host "  - $_" }
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: all KPI IDs are referenced in factsheets." -ForegroundColor Green
